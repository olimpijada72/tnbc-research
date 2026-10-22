#!/usr/bin/env python
"""Quick DeepSpot-M sanity check on a small slide region, for Apple Silicon Macs.

Instead of scoring a whole slide (tens of thousands of tiles), this cuts a small
square of N x N tiles from the most tissue-dense part of the slide, predicts a
handful of genes per tile on the Mac GPU (MPS), and writes:

  <out>/region.h5ad     spatial AnnData, same format as predict_wsi.py
  <out>/predictions.csv one row per tile: x, y, then one column per gene
  <out>/heatmaps.png    the H&E region next to one heatmap per gene

With no slide given, it downloads a small (~26 MB) open-access TCGA breast cancer
slide (TCGA-OL-A5RW-01Z-00-DX1) from the GDC portal and verifies its MD5.

The input should be a ~20x (~0.5 um/px) H&E slide: tiles are cut at native
resolution, matching how DeepSpot-M was trained. For a 40x slide pass
--downsample 2.

Needs pyvips, anndata and matplotlib:
    pip install -e "external/DeepSpotM[wsi]" "transformers>=4.43,<5" matplotlib

Examples:
  # demo breast slide, 8x8 tiles, default breast marker genes
  python scripts/quick_test_mac.py

  # your own slide, a 6x6 region, custom genes
  python scripts/quick_test_mac.py my_slide.svs --size 6 --genes ESR1 ERBB2 CD3D
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import urllib.request
from pathlib import Path

# Let ops without an MPS kernel fall back to CPU instead of erroring.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# predict_wsi.py (for to_anndata) lives in the pinned DeepSpotM copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "external/DeepSpotM/examples"))

# Hugging Face commit of ratschlab/DeepSpotM, same as in the Colab notebook.
HF_REVISION = "48be27af436a50e5c74175680ac2b7b2596a506b"

DEMO_UUID = "f2d5aa37-d9ce-4264-a447-fc69dd0d7d85"
DEMO_MD5 = "1a169f76fc7d21e767a93225968b9531"
DEMO_NAME = "TCGA-OL-A5RW-01Z-00-DX1.svs"

# ER, PR, HER2, proliferation, epithelium, immune, stroma
DEFAULT_GENES = ["ESR1", "PGR", "ERBB2", "MKI67", "EPCAM", "PTPRC", "COL1A1"]


def download_demo(dest_dir: Path) -> Path:
    path = dest_dir / DEMO_NAME
    if not path.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"downloading demo breast slide (~26 MB) to {path} ...", file=sys.stderr)
        urllib.request.urlretrieve(f"https://api.gdc.cancer.gov/data/{DEMO_UUID}", path)
    md5 = hashlib.md5(path.read_bytes()).hexdigest()
    if md5 != DEMO_MD5:
        raise RuntimeError(f"checksum mismatch for {path}: {md5}; delete it and retry")
    return path


def pick_region(slide, tile, size, white_mean):
    """Return (x0, y0) of the size x size tile window with the most tissue."""
    import numpy as np
    import pyvips
    from PIL import Image

    nx, ny = slide.width // tile, slide.height // tile
    if nx < size or ny < size:
        raise ValueError(f"slide is only {nx}x{ny} tiles; use a smaller --size")
    thumb = pyvips.Image.thumbnail_image(slide, nx)
    arr = np.ndarray(buffer=thumb.write_to_memory(), dtype=np.uint8,
                     shape=[thumb.height, thumb.width, thumb.bands])[..., :3]
    grid = np.asarray(Image.fromarray(arr).resize((nx, ny))).astype(np.float32).mean(2)
    tissue = (grid < white_mean).astype(np.float32)
    # sliding-window tissue count via a 2-D cumulative sum
    c = np.pad(tissue.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    win = c[size:, size:] - c[:-size, size:] - c[size:, :-size] + c[:-size, :-size]
    gy, gx = np.unravel_index(np.argmax(win), win.shape)
    return int(gx) * tile, int(gy) * tile


def save_heatmaps(region_rgb, coords, expr, genes, x0, y0, tile, size, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    n = len(genes) + 1
    cols = min(n, 4)
    rows = -(-n // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows), squeeze=False)
    axes = axes.ravel()
    axes[0].imshow(region_rgb)
    axes[0].set_title("H&E region")
    for i, g in enumerate(genes):
        grid = np.full((size, size), np.nan)
        for (x, y), v in zip(coords, expr[:, i]):
            grid[(y - y0) // tile, (x - x0) // tile] = v
        ax = axes[i + 1]
        im = ax.imshow(grid, cmap="viridis")
        ax.set_title(g)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([])
    for ax in axes[n:]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    plt.close(fig)


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="quick_test_mac.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("slide", nargs="?", help="whole-slide image (default: demo breast slide)")
    p.add_argument("--output", "-o", default="quick_test_out", metavar="DIR",
                   help="output folder (default: %(default)s)")
    p.add_argument("--genes", nargs="+", default=DEFAULT_GENES, metavar="GENE",
                   help="genes to predict (default: %(default)s)")
    p.add_argument("--size", type=int, default=8, metavar="N",
                   help="region is N x N tiles of 224 px (default: %(default)s)")
    p.add_argument("--x", type=int, help="region left edge in level-0 px (default: auto)")
    p.add_argument("--y", type=int, help="region top edge in level-0 px (default: auto)")
    p.add_argument("--downsample", type=float, default=1.0, metavar="F",
                   help="shrink the slide by F before tiling, e.g. 2 for a 40x slide")
    p.add_argument("--batch-size", type=int, default=4, metavar="N",
                   help="tiles per forward pass; lower it if MPS runs out of memory "
                        "(default: %(default)s)")
    p.add_argument("--white-mean", type=float, default=220.0, metavar="V",
                   help="mean pixel above which a tile counts as background")
    p.add_argument("--source", default="scgpt",
                   choices=["evo2", "orthrus", "prott5", "scgpt", "apertus"],
                   help="gene-embedding source (default: %(default)s)")
    p.add_argument("--device", choices=["mps", "cuda", "cpu"],
                   help="compute device (default: mps, else cuda, else cpu)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    # torch must be imported before pyvips: the other order segfaults on macOS
    # (Homebrew libvips) when the model weights load.
    import torch
    import numpy as np
    import pandas as pd
    import pyvips
    from PIL import Image

    from deepspotm import DeepSpotM
    from predict_wsi import to_anndata

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    slide_path = Path(args.slide) if args.slide else download_demo(Path("demo_data"))

    slide = pyvips.Image.new_from_file(str(slide_path), access="random")
    if args.downsample != 1.0:
        slide = slide.resize(1.0 / args.downsample)
    tile, size = 224, args.size
    if args.x is None or args.y is None:
        x0, y0 = pick_region(slide, tile, size, args.white_mean)
    else:
        x0, y0 = args.x, args.y
    print(f"slide {slide.width}x{slide.height}, region {size}x{size} tiles at "
          f"({x0}, {y0})", file=sys.stderr)

    region = slide.crop(x0, y0, tile * size, tile * size)
    rgb = np.ndarray(buffer=region.write_to_memory(), dtype=np.uint8,
                     shape=[region.height, region.width, region.bands])[..., :3]

    tiles, coords = [], []
    for r in range(size):
        for c in range(size):
            arr = rgb[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile]
            if arr.mean() <= args.white_mean:
                tiles.append(Image.fromarray(np.ascontiguousarray(arr)))
                coords.append((x0 + c * tile, y0 + r * tile))
    if not tiles:
        print("error: no tissue in this region; try other --x/--y", file=sys.stderr)
        return 1

    if args.device:
        device = args.device
    elif torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print(f"loading model on {device} ...", file=sys.stderr)
    model, proc = DeepSpotM.from_pretrained("ratschlab/DeepSpotM", source=args.source,
                                         revision=HF_REVISION)
    model = model.to(device).eval()
    missing = [g for g in args.genes if g not in set(model.gene_names)]
    if missing:
        print(f"error: genes not in the model panel: {missing}", file=sys.stderr)
        return 1

    print(f"predicting {len(args.genes)} genes for {len(tiles)} tissue tiles ...",
          file=sys.stderr)
    chunks, t0 = [], time.time()
    for i in range(0, len(tiles), args.batch_size):
        px = torch.stack([proc(im) for im in tiles[i:i + args.batch_size]]).to(device)
        with torch.no_grad():
            chunks.append(model.predict_genes(px, args.genes).float().cpu().numpy())
        done = min(i + args.batch_size, len(tiles))
        print(f"  {done}/{len(tiles)} tiles, {done / (time.time() - t0):.2f} tiles/s",
              file=sys.stderr)
    expr = np.concatenate(chunks, 0)
    coords = np.asarray(coords, int)

    adata = to_anndata(expr, coords, args.genes, slide_path, tile, args.source)
    adata.write_h5ad(out / "region.h5ad")
    df = pd.DataFrame(expr, columns=args.genes)
    df.insert(0, "y", coords[:, 1]); df.insert(0, "x", coords[:, 0])
    df.to_csv(out / "predictions.csv", index=False)
    save_heatmaps(rgb, coords, expr, args.genes, x0, y0, tile, size, out / "heatmaps.png")

    print(f"done in {time.time() - t0:.0f}s. Wrote {out}/region.h5ad, "
          f"predictions.csv, heatmaps.png", file=sys.stderr)
    print(df[args.genes].describe().loc[["mean", "min", "max"]].round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
