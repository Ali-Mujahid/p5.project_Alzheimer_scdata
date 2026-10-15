#!/bin/bash -l
#SBATCH --job-name=p5-ATAC-peak-TE
#SBATCH --partition=basic
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --output=ATAC-peak-TE-%j.out
#SBATCH --error=ATAC-peak-TE-%j.err
set -euo pipefail
[[ "$#" == 0 ]] || { echo 'No runtime arguments accepted'; exit 2; }
unset PYTHONPATH PYTHONHOME PYTHONOPTIMIZE
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
exec /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_RNA/analysis_environment/rna_py312/bin/python -B /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_peak_TE_annotation_20261015_v2/entry.py
