"""This app's GPU work, run through streetview_to_3d's one GPU entry point
(streetview_to_3d.gpu.run), so the street tab and this tab share one
decorated function.

Each task is a module-level function: ZeroGPU pickles it.
"""
import os
import tempfile
import time

import numpy as np

from streetview_to_3d import gpu
from streetview_to_3d.services.da3_ops import KEEP_RATE_THRESHOLD, run_da3

# One joint DA3 run on up to five panos (retried with fewer), then SHARP on
# six views and the alignment, both models already loaded. The Stockholm
# test took 81 s from click to splat, downloads included; see the
# "timing: splat" line to tighten this further.
SPLAT_GPU_S = 120


def _build_pipeline(device=None):
    from panoramic_to_3dgs import Pipeline
    from config import load_pipeline_config
    return Pipeline(load_pipeline_config(), device)


# On a Space, SHARP is loaded at startup on cuda, like DA3 in
# streetview_to_3d.gpu: ZeroGPU moves it onto the GPU for each call.
_pipeline = _build_pipeline("cuda") if gpu.ON_SPACES else None


def depth_around(target_path, neighbour_paths, cfg, views_base, da3):
    """Depth around one panorama: a single joint DA3 run on it and its
    same-date neighbours; the splat is scaled against these points.

    One joint run, not pairwise tests: there is nothing to chain, and DA3
    reconciles all of them at once. A neighbour that keeps under
    KEEP_RATE_THRESHOLD of its views -- the street walk's own link bar --
    is dropped and the run repeated without it. But fewer panos can also
    make DA3 worse on the target itself (on Stockholm it went 6/12 -> 1/12
    -> 0/12 as neighbours were dropped), so every run is kept and the one
    that keeps the most of the target's views wins.

    Returns a dict: points/colors (every kept pano's, in the target's run
    frame), pose (the target's (center, rotation)), views ((kept, total)
    for the target), n_clean (views surviving DA3's filter across the
    run), neighbours (the paths actually used).
    """
    target_id = os.path.basename(target_path)
    used, best = list(neighbour_paths), None
    for attempt in range(len(used) + 1):
        run_dir = os.path.join(views_base, f"around{attempt}")
        os.makedirs(run_dir, exist_ok=True)
        filtered, res, pts, cols, _, _ = run_da3(target_path, used, cfg, run_dir, da3=da3,
                                                 dist_thresh=0.2, angle_thresh=1)
        pose = res.pano_poses.get(target_id)
        run = {
            "points": pts if pts is not None else np.zeros((0, 3)),
            "colors": cols if cols is not None else np.zeros((0, 3)),
            "pose": (pose["center"], pose["rotation"]) if pose else None,
            "views": res.pano_keep_counts.get(target_id, (0, 0)),
            "n_clean": len(filtered),
            "neighbours": list(used),
        }
        print(f"depth_around: {len(used)} neighbour(s): target kept {run['views'][0]}/"
              f"{run['views'][1]}, {run['n_clean']} clean view(s) in all")
        if best is None or (run["views"][0], run["n_clean"]) > (best["views"][0], best["n_clean"]):
            best = run
        rate = {p: k / t if t else 0.0
                for p in used for k, t in [res.pano_keep_counts.get(os.path.basename(p), (0, 1))]}
        bad = [p for p in used if rate[p] < KEEP_RATE_THRESHOLD]
        for p in bad:
            print(f"depth_around: dropping neighbour {os.path.basename(p)} "
                  f"(kept {rate[p]:.0%} of its views)")
        if not bad:
            break
        used = [p for p in used if p not in bad]
    return best


def make_splat(image_path, neighbour_paths, output_dir, scale_mode):
    """Depth around the panorama (depth_around), then the
    splat scaled against it. Returns the splat's path."""
    global _pipeline
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as views:
        depth = depth_around(image_path, neighbour_paths, gpu.get_da3_config(),
                             views, gpu.get_da3())
    kept, total = depth["views"]
    print(f"depth: {len(depth['neighbours'])} neighbour(s) used, target kept {kept}/{total} views, "
          f"{len(depth['points']):,} points", flush=True)
    if _pipeline is None:
        _pipeline = _build_pipeline()
    _pipeline.config.scale_mode = scale_mode
    _pipeline.run(image_path, output_dir, depth)
    print(f"timing: splat {time.monotonic() - t0:.1f}s of {SPLAT_GPU_S}s", flush=True)
    return os.path.join(output_dir, "final_output.spz")
