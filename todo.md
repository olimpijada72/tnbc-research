# TODO

## Next steps

### 1. Check how well the model predicts your panel genes (public data)
- [ ] Pick a public breast dataset that has both H&E and real Visium measurements (10x FFPE breast Visium or HEST-1k)
- [ ] Run DeepSpot-M on it and line up the predicted tiles with the measured spots
- [ ] Compute predicted-vs-measured correlation for each of the 15 panel genes, plus EPCAM/KRT8/PTPRC
- [ ] Keep the genes that predict well, find substitutes for weak ones, and adjust the hypotheses to match

### 2. Lock the analysis plan
- [ ] Choose how to split tumour from stroma (EPCAM/KRT threshold, segmentation model, or pathologist)
- [ ] Define the niche scores and spatial metrics (e.g. CD8 in tumour vs stroma, CD276/SLC7A11-high fraction)
- [ ] Choose 2–4 primary endpoints and the statistical test, and commit the plan before unblinding

### 3. Build and test the pipeline
- [ ] Write the scoring and feature code in `src/`
- [ ] Test it end to end on the public slides from step 1

### 4. Prepare the cohort (in parallel)
- [ ] Ethics sign-off and de-identification
- [ ] Check scan resolution and file format, and run basic stain/tissue QC

---

## Full roadmap

1. Check how well the model predicts your panel genes (public data)
 - Pick a public breast-cancer dataset that has both H&E and real Visium measurements (10x FFPE breast Visium and/or HEST-1k breast samples)
 - Run DeepSpot-M on those slides through the existing Colab notebook
 - Line up the predicted tiles with the measured Visium spots
 - Compute predicted-vs-measured correlation for each of the 15 panel genes, plus EPCAM, KRT8 and PTPRC
 - Optional: sum predictions per slide for TCGA-BRCA TNBC cases and correlate with TCGA's bulk RNA-seq
 - Sort the genes into reliable / borderline / unreliable, and find substitutes for weak ones (e.g. CXCL9/10 in place of IFNG)
 - Revise the hypotheses to fit the genes that can actually be tested
2. Lock the analysis plan (before you see pCR labels)
 Choose how to split tumour from stroma: EPCAM/KRT threshold, a segmentation model, or pathologist annotation
 Define the niche scores: immune activation, checkpoint ligands, ferroptosis defence
 Define the spatial metrics: CD8 inside tumour vs in stroma, CD8–tumour contact/neighbourhood, fraction of CD276-high/SLC7A11-high tiles
 Choose 2–4 primary endpoints, the statistical test and the multiple-testing correction
 Write the plan into docs/ and commit it, so the git timestamp shows it came before unblinding
3. Build the analysis pipeline (src/)
 Load the .h5ad outputs and filter out low-quality tiles
 Compute the niche scores and the tumour/stroma split
 Compute the spatial metrics
 Combine everything into one feature table per patient
 Write the statistics/reporting script for pCR vs non-pCR
 Test the full pipeline end to end on the public slides from step 1
4. Prepare the cohort data
 Confirm ethics approval covers computational analysis of the slides
 De-identify the slides and build the patient ID ↔ clinical table link (stored off-repo)
 Check that scanner resolution (µm/px) and file format match what the model expects
 Run stain/blur QC and count usable tiles per biopsy
 Set exclusion criteria (e.g. minimum tissue area) and apply them blind to outcome
5. Run DeepSpot-M on the cohort
 Batch-run all pre-treatment biopsies on Colab and save the .h5ad files to Drive
 Spot-check the heatmaps against the H&E for a few slides
6. Validate against your own lab data
 Correlate per-patient predicted expression with RT-qPCR (CD8A, CD276, SLC7A11 and the others)
 Compare predicted CD8 localisation with IF on matched slides
 Note any genes where prediction and measurement disagree
7. Primary analysis
 Unblind pCR status
 Run the pre-specified pCR vs non-pCR comparisons
 Run the exploratory analyses, labelled as exploratory
 Make the figures: niche maps, per-patient scores, the validation plots
8. Write-up
 Methods (model version and weights revision from UPSTREAM.md)
 Results and limitations: prediction accuracy, cohort size, the small tissue area of core biopsies