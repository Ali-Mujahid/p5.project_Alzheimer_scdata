#!/bin/bash
#SBATCH --job-name=p5-ATAC-LSI-markers
#SBATCH --partition=basic
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=48:00:00
#SBATCH --output=/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2/embedding-%j.out
#SBATCH --error=/lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2/embedding-%j.err
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
exec /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_RNA/analysis_environment/rna_py312/bin/python -B /lisc/data/scratch/molecular_neurosciences/i-med/p5_Glial_TE_regulation_aging/pre_processed_ATAC/analysis_source/ATAC_embedding_20261014_v2/run_job.py
