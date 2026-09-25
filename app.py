"""Street View to 3D: a whole street as a placed point cloud, or one
panorama as a Gaussian splat.

The street tab is streetview_to_3d's own; the splat tab is splat_tab.py.
Both reach the GPU through streetview_to_3d.gpu, one decorated function.

Run locally:  python app.py
"""
# The package first: importing it imports `spaces` before anything touches
# CUDA, which ZeroGPU requires (see streetview_to_3d/gpu.py).
from streetview_to_3d.paths import DATA_DIR
from streetview_to_3d.ui.map_selection.tab import BRIDGE_CSS, BRIDGE_HEAD_SCRIPT
from streetview_to_3d.ui.tab import build_main_tab

import gradio as gr

from splat_tab import build_splat_tab

with gr.Blocks(title="Street View to 3D") as demo:
    gr.Markdown(
        "# Street View to 3D\n"
        "This Space provides two functions, from Google Street View and Apple Look Around panoramas:\n\n"
        "1. **Street → point cloud** (tab 1): a large-scale 3D point cloud of the street around the selected location.\n"
        "2. **Panorama → 3DGS** (tab 2): a small-scale 3D Gaussian splat of one panorama at the selected location.\n\n"
        "[[GitHub](https://github.com/YellowO2/streetview3d-app)]"
    )
    with gr.Tabs():
        with gr.Tab("Street → point cloud"):
            build_main_tab()
        with gr.Tab("Panorama → 3DGS"):
            build_splat_tab()


if __name__ == "__main__":
    demo.launch(
        allowed_paths=[DATA_DIR],
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Default(),
        css=".no-pad { padding-left: 0 !important; padding-right: 0 !important; } " + BRIDGE_CSS,
        head=BRIDGE_HEAD_SCRIPT,
        # Off: HF's default SSR adds a Node proxy in front of Python, and the
        # Space once hung on "restarting" behind it despite Python starting.
        ssr_mode=False,
    )
