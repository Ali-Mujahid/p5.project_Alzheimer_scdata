# Disease-directional Microglia TE heatmaps and UMAPs (24 October 2026)

This is an adaptation of the supplied TE-expression figure to five mouse groups: WT 3 mo, WT 6 mo, WT 21 mo, 5xFAD 3 mo, and APOE4/TREM2 3 mo. It uses existing, source-joined Microglia TE outputs and the saved full-atlas UMAP coordinates. The groups are conditions, not differentiation time points.

## Heatmaps

`results/RNA_TE_all_directional_heatmap.pdf` has all 241 tested RNA TE subfamilies with positive mouse-level edgeR log2 fold change in **both** 5xFAD vs WT 3 mo and APOE4/TREM2 vs WT 3 mo. `results/ATAC_TE_all_directional_heatmap.pdf` has all 585 tested subfamilies with positive mouse-level ATAC log2 fold change in both contrasts. These are separate assays. Each column is one of 20 mice; row colors are z scores of RNA TMM logCPM or log1p(ATAC TE fragments per million admitted unique fragments), respectively. Each PDF contains every selected row in consecutive pages. The overview PNGs show the first 35 rows ranked by minimum disease log2 fold change. TSVs contain every selected subfamily, both effect sizes/FDRs, and all 20 mouse values. `RNA_ATAC_150_shared_directional_subfamilies.tsv` gives their directional intersection.

**Neither assay has a positively changing TE subfamily at FDR < 0.1 in these contrasts.** The directional heatmaps therefore do not establish differential TE expression or accessibility. Mouse is the replicate; a cell is not a replicate. The two heatmaps use different count units, normalization and feature eligibility.

## UMAP examples

Three matched descriptive examples, `L1_Mm`, `IAPLTR3-int`, and `RMER12B`, each have a PDF/PNG with four rows and five group columns. Rows show the saved whole-atlas RNA UMAP, saved whole-atlas ATAC UMAP, Microglia gene-based RNA UMAP, and Microglia ATAC LSI UMAP. These are **four independent layouts**, not a joint co-embedding. Whole-atlas rows display a deterministic 30,000-point gray background of all cell types; only Microglia with measured TE values are colored. Each group column displays the cells of that condition. The projections are not recomputed from these selected TE features.

RNA color is log1p of a subfamily's IRescue expected UMI allocation per 10,000 total exported TE allocations within the cell. ATAC color is log1p of unambiguous TE-overlapping fragments per 10,000 admitted unique fragments. Both are relative/normalized measures with separate assay scales. Positive cells are colored; valid zero and background cells are gray. RNA cells with no usable exported TE exposure are excluded from the colored layer, not set to biological zero. Global coordinates were joined by original exact cell axis or verified selected row indices; Microglia coordinates were joined by exact cell ID and animal ID.

The RNA method assigns multimapping reads probabilistically to **TE subfamilies**, so these plots cannot resolve expression from an individual genomic TE copy. The ATAC matrix here is also subfamily-level; it does not depict locus-specific accessibility. These examples are directionally higher in both disease groups in both assays, but **all corresponding mouse-level FDRs exceed 0.1**. They are illustrations, not disease markers.

Sources and SHA-256s are in `results/manifest.json`. `build.py` regenerates all panels from the saved matrices, differential tables, source cell metadata and UMAP coordinates. Original BAMs, matrices and atlas embeddings are read-only.
