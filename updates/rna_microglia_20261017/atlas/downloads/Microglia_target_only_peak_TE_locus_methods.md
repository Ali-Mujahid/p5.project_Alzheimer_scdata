# Scaled Microglia TE RNA expression at ATAC peak-bound loci

The current figure uses scaled expression values. It supersedes the earlier plot whose y-axis showed normalized assigned UMI sums per 1,000 loci.

## Input loci and RNA data

The four target-only MAnorm peak-bound TE sets contain 9,361 WT_6mo, 9,725 WT_21mo, 7,240 5xFAD_3mo, and 6,438 APOE4_TREM2_3mo distinct mm10 TE loci. The paired WT_3mo-only peak-bound sets contain 8,188, 8,767, 10,136, and 10,615 loci. These use the unfiltered native unique-target/unique-control peak calls; no M or p-value cutoff was added. A TE copy can overlap distinct peaks from both sets.

Source expression is the previously validated Stellarscope 1.5 assigned-UMI matrix for 22,251 selected Microglia cells across 20 mice. Every selected ATAC TE locus joined uniquely to the RNA feature axis by chromosome, start, end, and strand. TE names differ in specificity between annotations, so the join uses coordinates. Feature-axis SHA256: `91c4d17962d10deab904f6fbd440f99d1d8c6d6a4f333db9f854ee9fcc0214ab`.

## Exact scaling

For each of the eight locus sets, use the same four WT_3mo and four target mice:

1. Normalize each locus's expression by the total assigned TE UMIs in that mouse: `TE-CPM = locus UMI / total assigned TE UMI × 1,000,000`.
2. Transform each locus and mouse with `x = ln(1 + TE-CPM)`.
3. For each locus, calculate `z = (x - mean(x across 8 mice)) / sample_SD(x across 8 mice)`.
4. Keep loci with zero variance, assigning their scaled value to zero for all mice.
5. For each mouse, average the locus z-scores over all loci in that fixed set. Boxplots summarize the four mouse values per condition. Circles are females and triangles males; each group has two of each.

The y-axis is **Scaled TE expression (mean locus z-score)**, a unitless relative expression score. Zero refers to the pairwise eight-mouse average. Positive scores represent higher relative locus expression, and negative scores lower relative expression. Averaging many loci narrows the score range; the displayed mouse mean scores themselves are not standardized to SD 1.

Scaling is done within each comparison and locus set. Values summarize relative patterns and do not measure absolute RNA abundance or fold change. Locus-wise scaling gives each variable locus the same variance before averaging, so its pattern can differ from the prior sum of assigned UMIs, which gives higher-count loci more weight. Constant loci remain in the denominator to preserve the full requested TE sets. Scaling sparse low-count loci can emphasize detection differences. No p-values or formal differential-expression conclusions are inferred from these plots. Stellarscope locus assignments remain model-based.

## Verification and files

Source locus sums exactly reproduce the validated mouse-level UMI sums for all 64 mouse/set rows. All variable locus z-scores have mean zero and sample SD one within numerical tolerance. Each comparison retains eight distinct mice with balanced sex. All eight panels share one y-axis range.

The scaled figure and exported values are in the local `results/scaled_expression` directory. The atlas provides the PDF, PNG, mouse scores and group median table. Original count matrices and the earlier normalized-UMI plot remain retained locally for provenance.
