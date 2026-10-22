# Upstream: DeepSpotM

This folder is an unmodified copy of DeepSpotM, kept here so this project does not
break when upstream changes.

| | |
|---|---|
| Code | https://github.com/ratschlab/DeepSpotM |
| Commit | `4d7793c890c500f51033444cc755f02b9d523628` (2026-09-04) |
| Copied | 2026-10-22 |
| Weights | https://huggingface.co/ratschlab/DeepSpotM |
| Weights revision | `48be27af436a50e5c74175680ac2b7b2596a506b` (2026-08-13) |

The weights are not stored here. `notebooks/colab_quickstart.ipynb` and
`scripts/quick_test_mac.py` download them at the revision above.

Code license: PolyForm Noncommercial 1.0.0 (`LICENSE`). Weights license:
CC-BY-NC-SA-4.0 (`WEIGHTS_LICENSE.md`). Research use only.

## Updating

Do not edit files here. To move to a newer upstream version:

```bash
git clone https://github.com/ratschlab/DeepSpotM /tmp/DeepSpotM
rm -rf external/DeepSpotM/* external/DeepSpotM/.[!.]*
git -C /tmp/DeepSpotM archive HEAD | tar -x -C external/DeepSpotM
```

Then restore this file (`git checkout HEAD -- external/DeepSpotM/UPSTREAM.md`), update the commit and date above, rerun the notebook demo,
and commit the update on its own.
