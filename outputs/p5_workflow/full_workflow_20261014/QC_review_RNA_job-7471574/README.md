# RNA-only QC review, job7471574

192successful library routes are verified (191original+repair35). Start with `review/QC_animal_review.pdf`, `review/QC_by_library.tsv`, `review/QC_by_animal_condition.tsv` and `review/all_library_thresholds.json`.

There are2,190,200unique conservative candidate IDs across20animals. These are not final singlets:1,469,390basic-supported nuclei (63.37%) have unresolved doublet status, and167/192libraries lack an automatic mitochondrial threshold. The candidate export includes1,410,621unresolved candidates. Preserve these flags for capture-aware sensitivity/retention review. No calibration group is entirely lost. Mitochondrial/doublet flag totals overlap and must not be added as disjoint removal counts.

The separate104ATACQC recovery and full296reconciliation are still pending. No final retention or normalization readiness is claimed. Original failedaccounting and the documented recovery35initial-admission SHA limitation remain preserved in the certificate. Downloaded product SHAvalues match the allocated producer.
