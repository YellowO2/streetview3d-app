"""This app's GPU work, run through streetview_to_3d's one GPU entry point
(streetview_to_3d.gpu.run), so the street tab and this tab share one
decorated function.

Each task is a module-level function: ZeroGPU pickles it.
"""
import os
import tempfile

from streetview_to_3d import gpu
from streetview_to_3d.services.da3_ops import depth_around

# DA3 load (~20 s), one joint DA3 run on up to five panos, then SHARP on
# six views and the alignment. The Stockholm test took ~2 min end to end.
SPLAT_GPU_S = 150

_pipeline = None


def make_splat(image_path, neighbour_paths, output_dir, scale_mode):
    """Depth around the panorama (streetview_to_3d's depth_around), then the
    splat scaled against it. Returns the splat's path."""
    global _pipeline
    with tempfile.TemporaryDirectory() as views:
        depth = depth_around(image_path, neighbour_paths, gpu.get_da3_config(),
                             views, gpu.get_da3())
    # SHARP needs the room
    gpu.release_da3()
    kept, total = depth["views"]
    print(f"depth: {len(depth['neighbours'])} neighbour(s) used, target kept {kept}/{total} views, "
          f"{len(depth['points']):,} points", flush=True)
    if _pipeline is None:
        from panoramic_to_3dgs import Pipeline
        from config import load_pipeline_config
        _pipeline = Pipeline(load_pipeline_config())
    _pipeline.config.scale_mode = scale_mode
    _pipeline.run(image_path, output_dir, depth)
    return os.path.join(output_dir, "final_output.ply")
