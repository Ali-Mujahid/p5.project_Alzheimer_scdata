# Microglia TE-age, ATAC, RNA and gene-density views (25 October 2026)

## Sources and meaning

- Genome: mm10 primary chromosomes 1–19, X and Y. RepeatMasker source: `canonical.rmsk.txt` on LiSC. LINE, LTR, SINE, DNA and RC annotations only. Lower divergence means `<10%` mismatch from the RepeatMasker consensus; higher divergence means `≥20%`. These are relative sequence-age proxies, **not dated insertion times**. Intermediate copies are omitted from the two age rings.
- ATAC: the user's 370,514-row 20-animal Microglia manual peak set, grouped by column 11. A TE copy is peak occupied when it overlaps at least one called peak from that group. The target-only BEDs contain peak-occupied TE copies with **no overlapping WT 3-month called peak**. They do not establish a statistically differential peak or absence of reads in control.
- The outer TE rings show, in 5 Mb bins, log₂(window peak-occupied copy fraction / genome-wide fraction for the same group and age bin). Empty bins have no defined log ratio and are gray. Color is capped at ±2 for display; exact copy counts and ratios are in the TSV. Gold ticks mark bins containing a target-only TE copy; opacity encodes count.
- ATAC signal is the exact mean of the five saved group `.bam.bw` files over each 5 Mb window. These group files are pooled coverage. The display uses a monotone log intensity; exact values are in the TSV.
- RNA ring is **group mean gene expression**, not basewise RNA coverage: mean log₂(CPM+1) over annotated genes in each 5 Mb window from the saved 55,487-gene five-group mouse-level Microglia RNA table. Gene density is the number of Gencode vM25 annotated genes per window. Chromosome placement uses gene midpoints. The small marker-window browser plot uses independently computed read depth from the 20 indexed animal Microglia RNA BAMs when that VSC calculation finishes.
- Four target Circos panels show WT 6 months, WT 21 months, 5xFAD 3 months and APOE4/TREM2 3 months. WT 3 months supplies the peak-call control for the target-only TE overlay. TE enrichment colors otherwise use each group's own genome-wide age-class baseline; they are **not** target-vs-control statistical tests.

## Browser windows

Four windows near `P2ry12`, `Tmem119`, `Apoe` and `Trem2` contain one illustrative TE copy beneath a target group peak and no WT 3-month peak overlap. Five ATAC group tracks use the saved pooled bigWigs. The RNA tracks use samtools depth from the 20 indexed animal-specific Microglia BAMs, MAPQ and base quality 20, 200-bp bins, normalized to each animal's mapped reads then averaged equally across the four animals per group. This is genomic RNA read depth, **not** a splice-aware gene-expression estimate or locus-specific TE transcription. Tracks share a y-axis within assay and window. The example TE–gene proximity does not prove a cis-regulatory link.

## Reproducibility and QC

`aggregate_te_age_accessibility.py`, `aggregate_atac_bigwigs.py`, `aggregate_rna_gene_density.py`, `extract_atac_browser_signal.py`, and the renderers generate the released TSV/BED/PDF/PNG files. LiSC jobs 7664651, 7664653 and 7664654 finished with exit 0. VSC RNA browser-depth job 8805786 was canceled before starting at the user's request. Basewise RNA coverage has not been added; the RNA ring shown here is gene-expression density.

Peak call counts vary between groups. No matched-depth peak calling, animal-level significance test or TE-locus RNA quantification was inferred from these descriptive plots.
