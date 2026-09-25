"""This app's GPU work, run through streetview_to_3d's one GPU entry point
(streetview_to_3d.gpu.run), so the street tab and this tab share one
decorated function.

Each task is a module-level function: ZeroGPU pickles it.
"""
import os
import tempfile
import time

from streetview_to_3d import gpu
from streetview_to_3d.services.da3_ops import depth_around

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


def make_splat(image_path, neighbour_paths, output_dir, scale_mode):
    """Depth around the panorama (streetview_to_3d's depth_around), then the
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
    return os.path.join(output_dir, "final_output.ply")
