# Quick test of DeepSpot-M on a Mac (Apple Silicon)

This runs DeepSpot-M on a small region of a breast cancer H&E slide using the Mac
GPU (MPS), to check that the install works. It is not a full-slide run.

It takes about 10 minutes on an 8 GB M-series MacBook. Most of that is loading the
model and predicting 64 tiles at about 0.15 tiles/s. A Mac with more memory will be
faster.

## 1. One-time setup

You need [Homebrew](https://brew.sh) and a Hugging Face account with access to
[ratschlab/DeepSpotM](https://huggingface.co/ratschlab/DeepSpotM). The repo is
gated, so open the page while logged in and accept the terms.

```bash
# system tools: libvips reads slides, uv manages Python
brew install vips uv

# clone and enter the repo
git clone https://github.com/olimpijada72/tnbc-research
cd tnbc-research

# Python 3.12 environment. Python 3.14 is too new for some ML packages.
uv venv --python 3.12 .venv
source .venv/bin/activate

# DeepSpot-M plus slide reading and plotting.
# Pin transformers below 5: with 5.x, loading the model fails with
# "Target modules {'query', 'key', 'value'} not found in the base model".
uv pip install -e "external/DeepSpotM[wsi]" "transformers>=4.43,<5" matplotlib

# log in to Hugging Face (paste a read token from https://huggingface.co/settings/tokens)
hf auth login
```

The first run downloads the 5.4 GB model into `~/.cache/huggingface`, and later
runs reuse it.

## 2. Run the quick test

```bash
source .venv/bin/activate        # if not already active
python scripts/quick_test_mac.py
```

This does the following:

1. Downloads a small (~26 MB) open-access TCGA breast cancer slide
   (`TCGA-OL-A5RW-01Z-00-DX1`) from the GDC portal into `demo_data/` and checks
   its MD5.
2. Picks the 8 x 8 tile (1792 x 1792 px) window with the most tissue.
3. Predicts 7 genes per 224 x 224 tile on MPS: ESR1, PGR, ERBB2, MKI67, EPCAM,
   PTPRC and COL1A1.
4. Writes these files to `quick_test_out/`:
   - `heatmaps.png`, the H&E region next to one heatmap per gene
   - `predictions.csv`, one row per tile with columns `x`, `y` and one per gene
   - `region.h5ad`, spatial AnnData in the same format as `predict_wsi.py`, so it
     opens in scanpy or squidpy

### What a working run looks like

```
slide 12879x13618, region 8x8 tiles at (4704, 672)
loading model on mps ...
predicting 7 genes for 62 tissue tiles ...
  4/62 tiles, 0.12 tiles/s
  ...
done in 423s. Wrote quick_test_out/region.h5ad, predictions.csv, heatmaps.png
```

Open `quick_test_out/heatmaps.png`. The maps should follow the tissue. In the demo
region, PTPRC (immune cells) is highest over the lymphocyte cluster at the top
right, COL1A1 (collagen) is high across the stroma, and epithelial genes are
highest near the ducts. If every map looks like flat noise, something is wrong.

## 3. Use your own slide

```bash
# your slide, default region and genes
python scripts/quick_test_mac.py path/to/slide.svs

# smaller region, your own genes, separate output folder
python scripts/quick_test_mac.py slide.svs --size 4 --genes ESR1 ERBB2 CD3D -o my_test

# choose the region yourself (top-left corner in full-resolution pixels)
python scripts/quick_test_mac.py slide.svs --x 20000 --y 15000
```

Run `python scripts/quick_test_mac.py --help` for all options.

### Check the magnification first

DeepSpot-M expects tiles at about **20x (~0.5 µm per pixel)**. The script cuts
tiles at the slide's native resolution and does not rescale automatically.

- **20x slide:** run as is.
- **40x slide (~0.25 µm/px):** add `--downsample 2`, otherwise each tile covers
  only a quarter of the tissue area the model expects.

You can usually find the magnification in the scanner software, or with:

```bash
vipsheader -a slide.svs | grep -iE "mpp|appmag|objective-power"
```

Some slides, including the demo slide, have no magnification metadata. In that
case, look at a full-resolution crop. At 20x a tumour cell nucleus is roughly
15–30 px across.

## Troubleshooting

| Problem | Fix |
|---|---|
| `NoMatchingPeftModuleError: Target modules {'query', 'key', 'value'} not found` | `uv pip install "transformers>=4.43,<5"` |
| Crash with exit code 139 (segfault) right after `loading model` | `torch` must be imported before `pyvips`. `quick_test_mac.py` already does this. In your own code, put `import torch` first. `external/DeepSpotM/examples/predict_wsi.py` imports `pyvips` first, so it hits this crash on macOS. |
| `MPS backend out of memory` | Lower `--batch-size` (try 2 or 1), use fewer `--genes`, or a smaller `--size` |
| Mac becomes very slow or swaps heavily | Close other apps. The model needs a few GB of memory. |
| `401` / `GatedRepoError` when downloading | Accept the terms on the HF model page, then run `hf auth login` |
| `genes not in the model panel` | Use HGNC symbols, e.g. `ERBB2` not `HER2`. The full list is `model.gene_names`, also in `tokens.csv`. |
| `no tissue in this region` | Pass a different `--x/--y`, or leave them out to use the automatic choice |

## Notes on the output

- Values are **predicted relative expression** (log1p-CPM scale), not measured
  counts. Compare tiles and regions within a slide, not absolute numbers.
- Each value covers one 224 x 224 tile (about 112 µm at 20x), so the resolution is
  close to a spatial transcriptomics spot, not single cells.
- This is the released base model. The published TCGA atlas used cancer-specific
  finetuned models that are not public, so expect softer maps than the atlas.
- Research use only. Code and weights are licensed for non-commercial use (see
  `external/DeepSpotM/LICENSE` and `external/DeepSpotM/WEIGHTS_LICENSE.md`).

## Going bigger

For a full slide, use `external/DeepSpotM/examples/predict_wsi.py` (see
`external/DeepSpotM/README.md`), or the Colab notebook.
A full slide has tens of thousands of tiles. At about 0.15 tiles/s on an 8 GB Mac
that takes days, so test the speed on your new Mac with `quick_test_mac.py` first.
On a Mac, also note the `pyvips` import-order crash above and add
`--genes` to keep memory down.
