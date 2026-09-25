"""The splat tab: one panorama, turned into a Gaussian splat.

Pick a spot, pick which capture of it (Google or Apple, and when), then
Generate. Depth comes from streetview_to_3d: the capture's own
panos at the neighbouring Street View nodes, run through DA3 together
(depth_around), so the splat is scaled against more than one viewpoint.
"""
import os
import shutil
import time
import uuid

import gradio as gr

from streetview_to_3d import gpu
from streetview_to_3d.paths import DATA_DIR, RUNS_DIR
from streetview_to_3d.reconstruct.around_pano import download, node_near, panos_around
from streetview_to_3d.services.geo import extract_lat_lon
from streetview_to_3d.ui.viewers import file_url

import tasks
import viewers

# Uploaded panoramas: not downloaded, so not in the shared pano cache.
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _label(capture):
    t = capture["target"]
    n = len(capture["neighbours"])
    return f"{'Apple' if t['source'] == 'apple' else 'Google'} · {t['date']} · {n} neighbour{'s' * (n != 1)}"


def _show(captures, i):
    """Download capture i at full resolution and make it the current pano."""
    target = captures[i]["target"]
    try:
        path = download(target, full_res=True)
    except Exception as e:
        raise gr.Error(f"Download failed: {e}")
    if not path:
        raise gr.Error("Download failed.")
    state = {"captures": captures, "choice": i, "image_path": path}
    return (viewers.build_map(target["lat"], target["lon"]),
            viewers.build_pano_viewer(file_url(path)), state)


def handle_load(url_input):
    try:
        lat, lon = extract_lat_lon(url_input)
        node, neighbours = node_near(lat, lon)
        captures = panos_around(node, neighbours)
    except ValueError as e:
        raise gr.Error(str(e))
    if not captures:
        raise gr.Error("No panorama found at that location.")
    map_html, pano_html, state = _show(captures, 0)
    choices = [(_label(c), i) for i, c in enumerate(captures)]
    return map_html, pano_html, state, gr.update(choices=choices, value=0, visible=len(choices) > 1)


def handle_select(state, choice):
    if not state or not state.get("captures") or choice is None or choice == state.get("choice"):
        return gr.update(), gr.update(), state
    return _show(state["captures"], choice)


def handle_upload(file_path):
    if not file_path:
        raise gr.Error("No file selected.")
    dest = os.path.join(UPLOADS_DIR, f"upload_{uuid.uuid4().hex}{os.path.splitext(file_path)[1] or '.jpg'}")
    shutil.copy(file_path, dest)
    state = {"captures": None, "image_path": dest}
    return viewers.build_pano_viewer(file_url(dest)), state


def handle_generate(state, scale_mode, progress=gr.Progress(track_tqdm=True)):
    if not state or not state.get("image_path"):
        raise gr.Error("Load or upload a panorama first.")
    yield viewers.SPLAT_PLACEHOLDER

    neighbours = []
    if state.get("captures"):
        for i, n in enumerate(state["captures"][state["choice"]]["neighbours"]):
            progress(0, desc=f"Downloading neighbour {i + 1}...")
            try:
                path = download(n)
            except Exception as e:
                print(f"neighbour {n['key']} failed to download: {e}")
                continue
            if path:
                neighbours.append(path)

    output_dir = os.path.join(RUNS_DIR, uuid.uuid4().hex)
    t0 = time.time()
    try:
        ply = gpu.run(tasks.make_splat, state["image_path"], neighbours, output_dir,
                      scale_mode, seconds=tasks.SPLAT_GPU_S)
    except Exception as e:
        raise gr.Error(f"Generation failed: {e}")
    if not ply or not os.path.exists(ply):
        raise gr.Error("Generation finished but produced no splat.")
    progress(1.0, desc=f"Done: {1 + len(neighbours)} pano(s), {time.time() - t0:.0f}s")
    yield viewers.splat_viewer_with_download(file_url(ply))


def build_splat_tab():
    state = gr.State(None)

    gr.Markdown("**1.** Paste a Google Maps link or upload a panorama → **2.** Pick a capture → **3.** Generate")
    with gr.Row(equal_height=True):
        url_input = gr.Textbox(placeholder="Google Maps URL or lat,lon (e.g. 1.3237, 103.7555)",
                               show_label=False, container=False, scale=5)
        load_btn = gr.Button("Load", variant="primary", scale=1, min_width=80)
        upload_btn = gr.UploadButton("Upload panorama (beta)", file_types=[".jpg", ".jpeg", ".png"],
                                     scale=1, min_width=80)

    capture_dropdown = gr.Dropdown(
        label="Capture",
        info="Every capture of this spot, Google and Apple, newest first. Its panos at the "
             "neighbouring nodes are used for depth.",
        choices=[], visible=False)

    with gr.Row(equal_height=True):
        map_view = gr.HTML(viewers.MAP_PLACEHOLDER, elem_classes="no-pad")
        pano_view = gr.HTML(viewers.PANO_PLACEHOLDER, elem_classes="no-pad")
    pano_download = gr.DownloadButton(label="⬇  Download current panorama", visible=False, size="sm")

    gr.Markdown("Generate the splat, ~2 min")
    with gr.Row(equal_height=True):
        scale_mode = gr.Dropdown(choices=["da3_y_ground", "da3_2dgrid_global"], value="da3_y_ground",
                                 label="Scale mode", info="How the splat is scaled against depth.", scale=2)
        generate_btn = gr.Button("Generate", variant="primary", scale=1, min_width=160)
    splat_view = gr.HTML(viewers.SPLAT_PLACEHOLDER)

    state.change(fn=lambda s: gr.update(visible=bool(s), value=(s or {}).get("image_path")),
                 inputs=[state], outputs=[pano_download])
    load_btn.click(fn=handle_load, inputs=[url_input],
                   outputs=[map_view, pano_view, state, capture_dropdown])
    capture_dropdown.change(fn=handle_select, inputs=[state, capture_dropdown],
                            outputs=[map_view, pano_view, state])
    upload_btn.upload(fn=handle_upload, inputs=[upload_btn], outputs=[pano_view, state]).then(
        fn=lambda: gr.update(choices=[], value=None, visible=False), outputs=[capture_dropdown])
    generate_btn.click(fn=handle_generate, inputs=[state, scale_mode], outputs=[splat_view],
                       show_progress="minimal", show_progress_on=[splat_view])
