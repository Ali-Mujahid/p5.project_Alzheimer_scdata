# ATAC LSI and independent marker diagnostics

Input: completed 7462166 raw mm10 peak and M25 gene-body activity matrices, 456472 initial fragment/TSS-QC nuclei, 68126 peaks. This additive stage preserves source matrices, all cells and unassigned calibration labels. No new fragment preparation, peak calling or counting.

One human-submitted allocation: 32 CPU, 128 GiB, 48 hours. The existing sparse-stage memory estimate is about 22 GB for raw peak arrays and working copies, before graph/runtime overhead; 128 GiB provides substantial buffer. Full-study embedding duration is unmeasured. No production ETA is promised. Gene activity is streamed in 10000-cell chunks after embedding, without loading its full matrix in memory.

Methods: existing tested sparse TF-IDF/LSI, 51 SVD components with first component saved for depth review and excluded from both 50-component neighbor graphs; 30 neighbors, Leiden resolution0.6, UMAP, seed1729. PCR library correction uses the pinned shape-aware Harmony API and verified connected technical design: every library crosses all20 animals/five conditions. The uncorrected comparator uses exactly the same LSI, features, components and graph settings. Raw integer CSR before/after digest is produced inside the allocation. Both graphs/clusters and independent equal-animal marker activity tables are diagnostic. This is a modern LSI adaptation, not a literal reproduction of published diffusion-map/densityPeak methods.

Gene-body accessibility is not RNA expression. Published labels calibrate only and do not assign fresh types. Missing panel genes do not prove absent cell types. All final doublet selection, FRiP policy, cell-type assignments, refined peaks and RNA label transfer remain pending actual cluster/marker/library review. RNA clusters6/13 remain provisional.

Guards: actual RUNNING account/owner/minimum CPU and memory; source manifest; accepted matrix identities and small terminal proofs; exclusive embedding lock; fixed605GB/53000inode scratch quota including in-doubt; one shared500GB/40000file RNA/ATAC output cap including prior attempts, monitored every30s by same-process own-FD storage observer; scoped termination and reaping. No stale partition whitelist. Large validation and science run only inside the human allocation. Runtime fixture tests must all pass without skips before science.

Submit once:

```bash
sbatch /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2/clustering.sbatch
```

Output: pre_processed_ATAC/analysis_runs/ATAC_embedding_20261014_v2/job-JOBID. Send the actual ID for monitoring. Do not duplicate or resubmit a partial run.
