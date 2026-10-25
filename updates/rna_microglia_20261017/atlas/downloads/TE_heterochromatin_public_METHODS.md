# Public heterochromatin reference tracks at Microglia TE loci

## Inputs and coordinate rules

The ATAC loci are mm10 TE copies from the 20-animal Microglia peak analysis. Each target set contains a TE copy below a called target-group peak and no overlapping WT 3-month **called peak**. WT 3-month peak-bearing TE copies form the reference peak set. This is a comparison of different sets of genomic loci. A missing WT peak does not mean no WT reads. A TE locus can occur in multiple target sets.

Full RepeatMasker mm10 TE annotations, TE age proxy and group-specific ATAC bigWig signals came from the verified Microglia Circos source. The per-locus tables and downloaded public files with SHA-256 manifests are retained on LiSC at `/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/analysis_runs/TE_heterochromatin_public_20261025/`.

| Mark | GEO | Published material | Method | Assembly | Role |
| --- | --- | --- | --- | --- | --- |
| H3K9me3 | [GSE317929](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE317929), GSM9483001–3/GSM9881351 | Control hippocampal Microglia, 3 weeks; four mice | ChIP-seq BigWig | mm10 | Primary external reference |
| CpG methylation | [GSE317924](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE317924), GSM9482908–9 | Control hippocampal Microglia, 3 weeks; two mice | WGBS CpG reports | mm10 | Primary external reference |
| H3K9me2 | [GSE288731](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE288731), GSM8774032–4 | E11.5 embryonic forebrain | CUT&RUN, 1-kb z-score bedGraphs | mm10 | Tissue-mismatched context only |
| H4K20me3 | [GSE153331](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE153331), GSM4640661/664 | Mouse embryonic stem-cell clones | ChIP-seq BigWigs | GRCm38.p5/mm10 | Cell-type-mismatched context only |

The deposited adult Microglia H3K9me3 CUT&Tag in [GSE309782](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE309782) uses mm39, and the 5xFAD/WT bulk prefrontal-cortex H3K9me2 in [GSE125850](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE125850) uses mm9. Neither was joined directly to mm10 TE copies.

## Measurements and plots

Public H3K9me3 and H4K20me3 BigWig signal is averaged over each TE interval, then the median across available public replicates is displayed. H3K9me2 is the median across three 1-kb z-score tracks. For each WGBS replicate, CpG methylation is coverage weighted within each TE interval; only TE copies with at least three CpGs and at least ten total reads in **each** replicate are plotted. The two replicate fractions are averaged. 3,835/67,953 TE copies meet this coverage rule. TE subfamily dot size counts measured loci, with group-specific reference medians as color. The Circos plot counts target-only TE copies in 10-Mb bins and scales each ring to its own 95th-percentile bin count. The TE-midpoint profile uses a deterministic 180-copy sample per group and four external H3K9me3 tracks.

Boxplots, density panels and TE-class heatmaps compare genomic-locus sets. Scatter panels use the same TE copy's log2((target ATAC + 0.01)/(WT 3-month ATAC + 0.01)) against the public reference mark, with locus-level Pearson r computed from all eligible values. Density and scatter displays are limited to the 1st–99th percentile of the reference mark for legibility; the summaries and Pearson calculations use all eligible values. The public mark is measured in different mice from ATAC. Copy-level n is **not** a biological-replicate sample size.

## Interpretation

5xFAD target-only TE copies have median public Microglia H3K9me3 signal 1.099 (n=8,398) versus 1.063 across WT 3-month peak-bearing copies (n=20,429); locus Pearson r is 0.017. This does not support lower *reference* H3K9me3 in the target set. Methylation is sparse and locus-set comparisons are affected by TE class, copy age, length, mappability and CpG density. None of these tracks establishes within-mouse heterochromatin loss, disease-specific mark change, chromatin escape or a causal relationship between mark and accessibility. The forebrain and stem-cell context panels cannot be read as Microglia profiles.

All data preparation and plotting jobs ran on LiSC. VSC job 8805786 was cancelled before starting; no VSC job was used for this analysis.
