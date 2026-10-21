# Global Figure 2 B/C/D architecture
Each dataset is the complete pinned peak-region universe; no cell matrix, cell-type DAR, motif enrichment or new MACS call was used.
Primary geometry is a 1 bp lower midpoint proxy: BED0 start+floor((end-start-1)/2), then [mid,mid+1). These are not MACS summits.
TE-copy genomic context also uses each full-reference TE copy's 1 bp lower midpoint. Full TE intervals are used for peak overlap, not substituted for centers.
Upper-center one-base sensitivity and full-peak-region overlap are exported separately. They are not pooled with primary geometry.
ChIPseeker transcript annotations use symmetric TSS +/-3000 bp, downstream option 300 bp, no strand restriction and no gene-symbol database mapping.
Nearest-TSS selection follows ChIPseeker's gene-associated transcript feature set (unlisted transcriptsBy(TxDb, by="gene")), rather than assuming every unconstrained TxDb transcript is eligible. Exon/intron context follows the separate TxDb annotation policy.
Priority: Promoter > 5UTR > 3UTR > Exon > Intron > Downstream > Intergenic
First/other exon and intron refer to the transcript ordinal in the actual ChIPseeker annotation; raw annotations are retained.
Venn units are the same peak IDs: any TxDb gene-body center hit versus any canonical-TE center hit, including neither. No-TE does not imply gene-associated.
Family bars count each peak ID once per canonical class|family, even for nested/multiple loci. Different families can overlap; fractions are nonexclusive.
Canonical family aliases and per-subfamily UNRESOLVED bins use the pinned taxonomy. Raw class|repFamily is retained separately.
Simple_repeat, Low_complexity, satellites and all other non-TE repeat classes are exported only in separately labelled descriptive tables.
Declared classes are DNA,LINE,LTR,RC,Retroposon,SINE; absent Retroposon is retained as zero in class summaries, not invented as an observed feature.
Published reciprocal95 coordinates retain assembly-conversion selection bias. No TE expression, autonomous TE activity, CATlas overlap or inferential enrichment is claimed.
