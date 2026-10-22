# Run DeepSpot-M on Google Colab

[`notebooks/colab_quickstart.ipynb`](../notebooks/colab_quickstart.ipynb) runs DeepSpot-M
on a free Colab GPU. It installs everything, checks the setup on a small demo
slide, then predicts every slide in a Google Drive folder and writes one `.h5ad`
per slide back to Drive.

## Once

1. Accept the terms of [ratschlab/DeepSpotM](https://huggingface.co/ratschlab/DeepSpotM)
   on Hugging Face (the model is gated), and create a read token at
   https://huggingface.co/settings/tokens.
2. Put your slides in a Drive folder, by default `MyDrive/deepspot/slides`. They
   should be ~20x (~0.5 µm/px) H&E.

## Each time

1. Open the notebook from GitHub with the *Open in Colab* badge in the README, or go
   to https://colab.research.google.com, choose *File → Open notebook → GitHub*, and
   enter `olimpijada72/tnbc-research`. To keep your settings, use *File → Save a copy
   in Drive*.
2. *Runtime → Change runtime type → T4 GPU*.
3. The first time only: click the key icon in the left sidebar, add a secret named
   `HF_TOKEN` with your token, and turn on notebook access.
4. Set the genes and folders in the *Settings* cell, then *Runtime → Run all*. Allow
   Drive access when asked.

Results go to `MyDrive/deepspot/output/<slide name>.h5ad` and open in scanpy or
squidpy. If the session disconnects, choose *Run all* again: finished slides are
skipped.

## Tips

- The notebook clones this repo at `REPO_REF` (default `main`) and loads the model
  at the Hugging Face commit `HF_REVISION`. For results you need to reproduce, set
  `REPO_REF` to a tag such as `v0.1`.

- The 5.4 GB model downloads again in each new session, which takes a few minutes.
  Tick `CACHE_MODEL_ON_DRIVE` to keep it on Drive instead.
- Leave `GENES` empty for the full ~19k-gene panel. Output files get much larger,
  and the free tier may run out of RAM on big slides.
- CUDA out of memory: lower `BATCH_SIZE`.
- On the free tier, long runs can be cut off. Colab Pro (L4 / A100) is faster and
  allows longer sessions.
