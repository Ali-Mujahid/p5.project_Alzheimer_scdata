# Genome-wide Microglia TE/ATAC/RNA tracks

The requested four contrasts are WT_6mo, WT_21mo, 5xFAD_3mo and
APOE4_TREM2_3mo, each shown against WT_3mo. Coordinates are mm10 primary
chromosomes 1–19, X and Y.

LiSC job **7665942** completed 0:0 in 32 seconds. It generated two verified
tracks:

- `results/mm10_TE_copy_density_1Mb.tsv.gz`: 2,737 bins plus header. Counts
  RepeatMasker LINE, SINE, LTR, DNA and RC intervals overlapping each 1 Mb
  window. The full source contains 5,138,236 RepeatMasker records, of which
  3,651,522 selected TE intervals were measured. A copy crossing a bin edge
  contributes to both bins.
- `results/Microglia_ATAC_group_bigWig_signal_100kb.tsv.gz`: 27,268 bins plus
  header, with exact mean of each saved group `.bam.bw` over 100 kb windows.
  These are pooled group bigWig signals from `te-atac`, not four independent
  animal values or a differential test.

Both compressed TSVs passed `gzip -t`; their local SHA-256 values match the
LiSC products: ATAC `527dce27f4c248a91dad1e80f19afa5c2d833245205032fd5a688c465d55d757`,
TE density `2894f530281d2e4e33d1b76eb91ab798b1255bb1389635de2f05b1188ab2d162`.
The four-page PDF and four PNGs show the actual TE and ATAC tracks. The
accessibility plot uses log1p display scaling; TSV values remain unchanged.

**RNA TE layer is pending.** Existing IRescue results are subfamily expected
UMI counts and cannot be placed at individual genome coordinates. VSC
20-animal copy-overlap array 8806092 was still `PENDING (Priority)` at the
last observation. `aggregate_rna_te_windows.py` is staged on LiSC to form
100 kb RNA TE-copy overlap tracks once all 20 selected-Microglia count files
are verified and transferred. It normalizes each animal by selected primary
alignments, then averages four mice equally per group. That endpoint is
*primary RNA alignment overlap at TE copies*, not IRescue UMI expression or
uniquely localized TE transcription. The renderer accepts it as `--rna` and
will produce three stacked tracks per contrast without fabricating the
currently missing layer.
