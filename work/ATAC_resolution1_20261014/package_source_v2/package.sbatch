#!/bin/bash -l
#SBATCH --job-name=p5-ATAC-res1-package
#SBATCH --partition=basic
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=ATAC-res1-package-%j.out
#SBATCH --error=ATAC-res1-package-%j.err
set -euo pipefail
[[ "$#" == 0 ]] || { echo 'This finite package stage accepts no input arguments'; exit 2; }
unset PYTHONPATH PYTHONHOME PYTHONOPTIMIZE
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
exec /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_RNA/analysis_environment/rna_py312/bin/python -B /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_resolution1_package_20261015_v2/package_entry.py
