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

A Gradio app that hosts two projects in one [Hugging Face Space](https://huggingface.co/spaces/potato-bug/street-view-to-3dgs):

1. **Street → point cloud**: [streetview-to-3d](https://github.com/YellowO2/streetview-to-3d)
2. **Panorama → 3DGS**: [panoramic-to-3dgs](https://github.com/YellowO2/panoramic-to-3dgs)

## Run locally

Requires an NVIDIA GPU and Python 3.12.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
# torch + torchvision for your CUDA version (see `nvidia-smi`), e.g. CUDA 12.4:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python app.py
```

## License

MIT.
