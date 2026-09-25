---
title: Street View To 3D
emoji: 🌖
colorFrom: pink
colorTo: indigo
sdk: gradio
sdk_version: 6.15.2
python_version: '3.12'
app_file: app.py
pinned: false
license: mit
short_description: Street View panoramas into point clouds and 3DGS scenes
---

# Street View to 3D

Turn Google Street View and Apple Look Around panoramas into 3D, in two ways:

- **Street → point cloud**: pick a stretch of street on the map; its panoramas are linked with Depth Anything 3 and placed on the real road as one point cloud.
- **Panorama → 3DGS**: pick one panorama (any Google or Apple capture of a spot), optionally edit it with FLUX, and turn it into a Gaussian splat with Apple SHARP, scaled against DA3 depth from the same capture's neighbouring panoramas.

Try it on [Hugging Face](https://huggingface.co/spaces/potato-bug/street-view-to-3dgs). This repo is only the app; the work is done by:

- [streetview-to-3d](https://github.com/YellowO2/streetview-to-3d): fetching panoramas, the street reconstruction, depth around one panorama, and the GPU entry point both tabs share
- [panoramic-to-3dgs](https://github.com/YellowO2/panoramic-to-3dgs): one panorama plus depth into a splat
- [panoramic-da3](https://github.com/YellowO2/panoramic-da3): Depth Anything 3 on panoramas

<table>
<tr>
<td align="center"><sub>Demo Video</sub></td>
<td align="center"><sub>Comparison with HunyuanWorld 2.0 + World Marble 1.1</sub></td>
</tr>
<tr>
<td width="50%"><a href="https://youtu.be/mzIDZWxv4vA"><img src="https://img.youtube.com/vi/mzIDZWxv4vA/hqdefault.jpg" alt="Demo video"></a></td>
<td width="50%"><a href="https://youtu.be/fYANbQXMZ_0"><img src="https://img.youtube.com/vi/fYANbQXMZ_0/maxresdefault.jpg" alt="Comparison with HunyuanWorld 2.0 + World Marble 1.1"></a></td>
</tr>
</table>

## Run locally

Requires an NVIDIA GPU with recent drivers and Python 3.12.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
# torch + torchvision matching your CUDA version (see `nvidia-smi`), e.g. CUDA 12.4:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python app.py
```

Models (DA3, SHARP, FLUX) download from the Hugging Face Hub on first use. Everything the app writes goes under `./data` (set `STREETVIEW_TO_3D_DATA` to move it).

## Acknowledgments

This project relies on:

- [Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) (Apache 2.0)
- [Apple ml-sharp](https://github.com/apple/ml-sharp) (Apple sample code license)
- [FLUX.2-klein](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B) (Black Forest Labs)
- [flux-2-klein-4B-object-remove-lora](https://huggingface.co/fal/flux-2-klein-4B-object-remove-lora) (fal)

## License

MIT.
