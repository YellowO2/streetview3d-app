"""This app's GPU work, run through streetview_to_3d's one GPU entry point
(streetview_to_3d.gpu.run), so the street tab and this tab share one
decorated function and one loaded DA3.

Each task is a module-level function: ZeroGPU pickles it.
"""
import os
import tempfile

from streetview_to_3d import gpu
from streetview_to_3d.services.da3_ops import depth_around

# DA3 load (~45 s cold), one joint DA3 run on up to five panos, then SHARP
# on six views and the alignment.
SPLAT_GPU_S = 150
# FLUX over a panorama in overlapping chunks.
EDIT_GPU_S = 72

_pipeline = None
_flux = None
if gpu.ON_SPACES:
    # Loaded at startup on a Space, where ZeroGPU moves it onto the GPU
    # for each call; loading inside the call would spend the window on it.
    from editors.flux_editor import FluxEditor
    _flux = FluxEditor(offload=False)


def make_splat(image_path, depth_image_path, neighbour_paths, output_dir, scale_mode):
    """Depth around the panorama (streetview_to_3d's depth_around), then the
    splat scaled against it. depth_image_path is the unedited panorama when
    image_path has been edited. Returns the splat's path."""
    global _pipeline
    with tempfile.TemporaryDirectory() as views:
        depth = depth_around(depth_image_path, neighbour_paths, gpu.get_da3_config(),
                             views, gpu.get_da3())
    # SHARP needs the room, next to FLUX
    gpu.release_da3()
    kept, total = depth["views"]
    print(f"depth: {len(depth['neighbours'])} neighbour(s) kept, target kept {kept}/{total} views, "
          f"{len(depth['points']):,} points", flush=True)
    if _pipeline is None:
        from panoramic_to_3dgs import Pipeline
        from config import load_pipeline_config
        _pipeline = Pipeline(load_pipeline_config())
    _pipeline.config.scale_mode = scale_mode
    _pipeline.run(image_path, output_dir, depth)
    return os.path.join(output_dir, "final_output.ply")


def edit_pano(image_path, prompt, mode, output_path):
    global _flux
    if _flux is None:
        from editors.flux_editor import FluxEditor
        _flux = FluxEditor(offload=True)
    _flux.edit(image_path, prompt, mode=mode, output_path=output_path)
    return output_path
