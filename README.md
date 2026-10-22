# TNBC Spatial Immunity
![Python](https://img.shields.io/badge/python-3.12-blue)
![Model](https://img.shields.io/badge/model-DeepSpot--M-green)
![License](https://img.shields.io/badge/license-MIT-purple)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1uLjie8uztSPUCQbfdpZbUVRpAy5-0EfZ#scrollTo=il4XmJWtYIGG)

Virtual spatial transcriptomics of pre-treatment biopsies in triple-negative breast
cancer (TNBC), to look for predictors of response to neoadjuvant chemo-immunotherapy
(paclitaxel, carboplatin and pembrolizumab).

## Overview

This repository holds the computational part of a translational TNBC study. The study
samples patients at three points: blood (PBMC) and a diagnostic core-needle biopsy
before therapy, the surgical specimen after therapy (pCR vs. non-pCR), and the
residual tumour in non-pCR patients. RT-qPCR and immunofluorescence measure bulk
expression, but they do not show *where* cells and transcripts sit in the tissue.

To add the spatial view, we run [DeepSpot-M](https://github.com/ratschlab/DeepSpotM),
which predicts spatial gene expression from routine H&E slides, on the pre-treatment
FFPE biopsies. The question:

> Does the spatial organisation of immune and ferroptosis-related niches in the
> diagnostic biopsy separate patients who reach pathological complete response (pCR)
> from those with residual disease?

The full study proposal and analysis plan, in Serbian, are in [`docs/`](docs/).

## Hypotheses

1. **pCR tumours have more immune-active niches.** Tumour regions show high
   CD8A/CD8B, IFNG, CXCL9/CXCL10 and GZMB/PRF1, with TILs in direct contact with tumour,
   and low SLC3A2/SLC7A11/GPX4 in those same zones.
2. **Non-pCR tumours have immune-excluded or immune-suppressed niches.** CD8 cells stay
   mostly in the stroma, alternative checkpoint ligands (CD276, VTCN1, HLA-E, CD47) are
   high, IFNG/GZMB/PRF1 stay low despite TILs, and SLC3A2/SLC7A11/GPX4 is high in tumour
   regions. In short: *immune-infiltrated, but functionally suppressed and
   ferroptosis-resistant*.
3. **CD276-high / SLC7A11-high niches predict residual disease.** These are regions
   with high CD276 and SLC3A2/SLC7A11/GPX4, a low IFNG/cytotoxic score, and weak CD8–tumour
   contact.

The idea behind 1–3: IFNγ from CD8⁺ T cells downregulates SLC7A11/SLC3A2 in tumour
cells, which makes them more sensitive to ferroptosis.

## Gene panels

| Program | Genes |
|---|---|
| Immune activation | CD8A, CD8B, IFNG, CXCL9, CXCL10, GZMB, PRF1 |
| Alternative checkpoint ligands | CD276 (B7-H3), VTCN1 (B7-H4), CD47, HLA-E, TNFRSF14 (HVEM) |
| Ferroptosis defence | SLC7A11, SLC3A2, GPX4 |

## Running DeepSpot-M

**Google Colab (recommended).** Click the *Open in Colab* badge above, or follow
[`docs/setup_colab.md`](docs/setup_colab.md). You need a Hugging Face token with access
to the gated [ratschlab/DeepSpotM](https://huggingface.co/ratschlab/DeepSpotM) model
and your slides in a Google Drive folder. The notebook writes one `.h5ad` per slide
back to Drive.

**Mac (small-region test only).** See [`docs/setup_mac.md`](docs/setup_mac.md). A
whole slide is far too slow on a laptop.

### Reproducibility

DeepSpot-M is vendored in [`external/DeepSpotM/`](external/DeepSpotM/) at a fixed
upstream commit, and the weights are loaded at a fixed Hugging Face revision. Both are
recorded in [`external/DeepSpotM/UPSTREAM.md`](external/DeepSpotM/UPSTREAM.md), so
changes to the original repositories cannot break or silently change our results.

## Repository layout

```
├── docs/                   study proposal, analysis plan, setup guides
├── notebooks/              Colab notebook for running DeepSpot-M
├── scripts/                helper scripts (Mac quick test)
└── external/DeepSpotM/     pinned, unmodified copy of DeepSpot-M
```

Analysis code (niche scoring, pCR vs. non-pCR comparison) will go in `src/`.

## Data

No patient data is stored in this repository. Slides, `.h5ad` outputs and clinical
tables stay on Google Drive or local disk, and `.gitignore` blocks the common slide
and output formats.

## Licenses

- Code in this repository: MIT (see [`LICENSE`](LICENSE)).
- `external/DeepSpotM/`: PolyForm Noncommercial 1.0.0. The DeepSpot-M weights are
  CC-BY-NC-SA-4.0. Both are research and non-commercial use only. See the license
  files in that folder.

## Citation

If you use DeepSpot-M, cite the original work; see
[`external/DeepSpotM/CITATION.cff`](external/DeepSpotM/CITATION.cff).
