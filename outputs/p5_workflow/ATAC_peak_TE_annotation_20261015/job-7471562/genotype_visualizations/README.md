# TE coordinate overlap across genotype and age cohorts

Verified producer job 7471562. These figures describe the fraction of **callable peak-union base pairs** overlapping RepeatMasker TEs, with equal animal weight. They do not measure TE expression or per-cell accessibility and do not test genotype effects. Cell types are the original peak-discovery calibration groups, not final independent annotations.

Microglia has 20 callable animal groups: five conditions, four animals each (2 female, 2 male). The 3-month genotype boxplot compares WT, 5xFAD and APOE4/TREM2 only; older WT is displayed separately on heatmaps. Point metadata, peak counts and denominator bp are saved in the TSV. NA is retained for absent or empty groups across all cell types. Class/family/subfamily overlap categories can overlap and do not form a composition that must sum to 100%.

The full family/subfamily tables remain in `all_types_taxonomy_by_condition_equal_animal_summary.tsv.gz` and `microglia_all_taxonomy_animal_details.tsv.gz`; top-20 displays are chosen descriptively by all-animal mean coverage. PDFs are the download format; PNGs are previews only. Native RepeatMasker repFamily is called family; subclass is a display alias.
