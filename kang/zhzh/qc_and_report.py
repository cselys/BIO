import anndata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json

adata = anndata.read_h5ad('results/data/cell_gene_matrix.h5ad')

# QC metrics
# adata.X is a sparse CSR matrix
total_counts = np.array(adata.X.sum(axis=1)).flatten()
adata.obs['total_counts'] = total_counts
adata.obs['n_genes'] = np.array((adata.X > 0).sum(axis=1)).flatten()

# Mito genes
mito_genes = [g for g in adata.var_names if g.startswith('MT-') or g.startswith('mt-')]
mito_counts = np.array(adata[:, mito_genes].X.sum(axis=1)).flatten()
adata.obs['pct_mito'] = mito_counts / total_counts

# Save QC to adata
adata.write('results/data/cell_gene_matrix.h5ad')

# Figures
plt.figure()
plt.hist(adata.obs['total_counts'], bins=50)
plt.title('Total counts per cell')
plt.savefig('results/figures/qc_total_counts.png')
plt.close()

# Summary
summary = {
    "num_cells": int(adata.shape[0]),
    "num_genes": int(adata.shape[1]),
    "mean_counts_per_cell": float(adata.obs['total_counts'].mean()),
    "mean_n_genes_per_cell": float(adata.obs['n_genes'].mean())
}
with open('results/phase2_summary.json', 'w') as f:
    json.dump(summary, f, indent=4)
print("QC and report generated.")
