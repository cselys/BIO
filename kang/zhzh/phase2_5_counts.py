import pandas as pd
import numpy as np
import json
import os
from tqdm import tqdm
from scipy import spatial

# Load transformation
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Load AnnData to get assigned counts
import anndata
adata = anndata.read_h5ad('results/data/cell_gene_matrix.h5ad')

# 1. Count Recovery (using summary + full scan of GEM if needed)
# Re-stream to get TOTAL MIDCounts and UNASSIGNED counts (or compute from Phase 2)
# Phase 2 stats (total assigned vs total_midcounts) can be recomputed.
gem_file = 'FP200000489TL_B5.gem'
total_midcounts = 0
total_spots = 0

# (Simplified: reuse the count from previous runs for total, or re-run)
# I'll just re-stream to be safe and rigorous.
print("Streaming GEM for total counts...")
with open(gem_file, 'r') as f:
    f.readline()
    for line in tqdm(f):
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        total_midcounts += int(parts[3])
        total_spots += 1

assigned_midcounts = adata.X.sum()
assigned_spots = adata.X.sum(axis=1).sum() # Wait, this is counts not spots
# Actually, I have triplets from Phase 2 (the CSVs)
assigned_triplets_dir = 'results/data/temp_triplets'
assigned_counts = 0
assigned_spots = 0
for f in os.listdir(assigned_triplets_dir):
    df = pd.read_csv(os.path.join(assigned_triplets_dir, f))
    assigned_counts += df['count'].sum()
    assigned_spots += len(df)

recovery_stats = {
    "total_spots": total_spots,
    "assigned_spots": assigned_spots,
    "unassigned_spots": total_spots - assigned_spots,
    "pct_spots_assigned": (assigned_spots / total_spots) * 100,
    "total_midcounts": total_midcounts,
    "assigned_midcounts": int(assigned_counts),
    "unassigned_midcounts": total_midcounts - int(assigned_counts),
    "pct_midcounts_assigned": (assigned_counts / total_midcounts) * 100,
    "num_annotated_cells": len(df_annot),
    "cells_with_expression": adata.obs['total_counts'].gt(0).sum(),
    "pct_cells_with_expression": (adata.obs['total_counts'].gt(0).sum() / len(df_annot)) * 100
}

# Handle numpy types for JSON
def convert_numpy(o):
    if isinstance(o, (np.int64, np.int32)): return int(o)
    if isinstance(o, (np.float64, np.float32)): return float(o)
    return o

with open('results/phase2_5_summary.json', 'w') as f:
    json.dump(recovery_stats, f, indent=4, default=convert_numpy)

print("Count recovery metrics saved.")
