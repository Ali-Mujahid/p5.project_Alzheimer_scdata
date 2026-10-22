# GSE212606 mouse RNA, ATAC and TE atlas

A complete, portable snapshot of the interactive atlas and the files needed to operate it. It includes the browser source, all offline libraries and licenses, UMAP coordinates, Leiden0.6/1.0 labels and marker adapters, all28 TE-overlap views, downloadable PDF/TSV reports, build and validation scripts, archived producer source and provenance.

**Reviewed update: 21 October 2026.** The current atlas includes provisional RNA labels, Microglia review tables, ATAC TE results, and reviewed mouse-level Microglia RNA TE results and figures. Labels and core-analysis membership remain provisional. Saved-coordinate availability is stated by the adapter; unavailable points are not replaced or synthesized. The dated ATAC QC observation is 100 of 104 libraries; this does not establish final retention or a current scheduler state.

The complete **15 October 2026 base snapshot** remains immutable and can be opened separately with `--base-snapshot`. Its historical QC observations are dated archival evidence, including the earlier 8-library import; they are not the current status. Final labels, RNA–ATAC transfer and whole-atlas TE analysis remain pending.

## Open the atlas online

[Open the interactive atlas on GitHub Pages](https://ali-mujahid.github.io/p5.project_Alzheimer_scdata/). The link works without downloading the repository or running a local server.

## Open an offline copy on another computer

1. Download **Code → Download ZIP** and extract it, or clone:

   ```bash
   git clone https://github.com/Ali-Mujahid/p5.project_Alzheimer_scdata.git
   cd p5.project_Alzheimer_scdata
   ```

2. With Python3.10 or later, run:

   ```bash
   python3 start_atlas.py --open
   ```

   On Windows use `py -3 start_atlas.py --open`, or double-click `Start_atlas.bat`. On macOS, `Start_atlas.command` is also included.

3. The launcher restores the included data, checks SHA-256 identities and serves:

   **http://127.0.0.1:56404/full_workflow_20261014/atlas_preview/index.html#rna**

   If that port is already in use: `python3 start_atlas.py --port 56405 --open`. Press Ctrl+C in the terminal to stop.

Offline viewing uses only Python's standard library and a modern browser. No R, scientific Python packages, cluster login, Internet/CDN or additional data download is needed after obtaining the repository. Opening the HTML with `file://` does not support its lazy JSON loading; use the launcher.

To view the original archived interface, run `python3 start_atlas.py --base-snapshot --open`. This explicitly ignores the overlay, including a damaged overlay, and uses the unchanged original files. Without that option, an invalid overlay stops startup; it never silently falls back to old scientific status.

## What is included

- **1,356 original files;425,980,648uncompressed bytes.** Every selected original byte is preserved.
- **224 source/small-metadata files** are directly browsable under `work/` and `outputs/`.
- The complete snapshot is losslessly compressed into59 ordered parts under `snapshot/` (246,629,796bytes). This keeps individual GitHub objects small. The launcher reconstructs every original path automatically; no Git LFS or external storage account is required.
- `snapshot/FILES.json` lists every file's relative path, byte size and SHA-256. `snapshot/manifest.json` binds that inventory and every archive part.
- `updates/current.json` is the explicit schema 2 overlay manifest. It binds the original `snapshot/FILES.json` hash and lists every updated HTML, JavaScript, stylesheet, data and download route with its exact relative path, byte size and SHA-256. These additive files are separate from the 59 base archives and original file inventory.
- The RNA label-code `.npy` download preserves the original accepted source-cell order. Its codebook/provenance bind the exact source metadata hash; use that same metadata before joining labels to cells. NumPy is not needed to view the atlas. Original preview PNGs and clearly identified raster-preview PDFs preserve the saved diagnostic pixels; they do not rerun a plot or create new annotations.
- `outputs/p5_workflow/` is the original HTTP document root. Relative layout and original scientific source manifests are preserved. Four original producer source sets include every42 manifest member, including their archival Slurm scripts.
- `work/` contains the initial adapter/coordinate/Leiden import scripts, TE plot/adapters, QC status builder, tests and related scientific source. Original scientific scripts retain their actual historical cluster paths; they are archival code, not portable reruns of the full biological analysis.

Raw FASTQ/BAM files and the unused1.63GB H5AD are outside the browser's dependency closure and remain in the original project/LiSC storage. All coordinates and summaries the browser actually uses are included. Large source matrices would be required to rerun upstream scientific producers; they are not required to operate this snapshot. OS metadata, SSH sockets and credentials are excluded.

## Verify or restore manually

```bash
python3 atlas_snapshot.py --restore
python3 atlas_snapshot.py
python3 start_atlas.py --check
python3 start_atlas.py --base-snapshot --check
```

Restoration checks every compressed part and every extracted file, rejects unexpected paths and preserves any existing file whose contents differ. The verification command reports missing or changed files. The launcher verifies the complete declared overlay before serving; each overlay response is checked again and served from the verified byte string. Changed overlay bytes cause an error response rather than exposing an old base asset at that route. No original archive or inventory is rewritten. This repository is not a live connection to LiSC.

## Scientific interpretation

- Initial ATAC contains456,472nuclei,20animals and104libraries. All supported, rare and unknown cell types remain in scope; Microglia has additional views.
- RNA broad labels, the10-group Microglia review and the core-analysis selection are accepted provisional review products. Display edits do not modify original labels, counts or analysis membership. Mixed/BAM-like and other conflicting identities stay visible; Allen fine labels, disease states and final singlet certification are not established.
- Gene-body activity measures accessibility, not RNA expression. The107-gene panel is descriptive, not genome-wide differential marker discovery.
- TE heatmaps/animal boxplots describe RepeatMasker coordinate overlap with initial calibration-type peak sets. They do not establish TE expression, fragment-count accessibility, matched-background enrichment or genotype significance.
- Candidate QC is not final singlet certification. Unsupported mitochondrial/doublet thresholds remain explicit. New filtered biological views are unavailable until their actual gates pass.
- Animals are biological replicates. Older WT mice are not pooled as young disease controls.
- Every interactive plot download remains **PDF**. TSV/JSON exports are data/label exports. Existing PNG files are archived report previews, not the atlas plot export format.

## Rebuilding and licenses

The ready snapshot needs no build step. For optional adapter/figure development, see `docs/BUILD_AND_PROVENANCE.md`. Original scientific and builder bytes are archived unchanged, including historical absolute paths and evidence hashes. Rebuilding requires explicit input/path binding and produces a new provenance record; changing browser display labels does not create final scientific annotation.

Vendored Chart.js4.5.1 and jsPDF4.2.1 retain their original MIT notices. No new license is asserted over the original study data or the entire research project.
