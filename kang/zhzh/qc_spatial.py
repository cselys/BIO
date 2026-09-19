import anndata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os

adata = anndata.read_h5ad('results/data/full_tissue_bins.h5ad')

# QC metrics
adata.obs['total_counts'] = np.array(adata.X.sum(axis=1)).flatten()
adata.obs['n_genes'] = np.array((adata.X > 0).sum(axis=1)).flatten()

# Mito genes
mito_genes = [g for g in adata.var_names if g.startswith('MT-') or g.startswith('mt-')]
mito_counts = np.array(adata[:, mito_genes].X.sum(axis=1)).flatten()
adata.obs['pct_mito'] = mito_counts / adata.obs['total_counts']
adata.obs['pct_mito'] = adata.obs['pct_mito'].fillna(0)

# Save
adata.write('results/data/full_tissue_bins.h5ad')

# Spatial maps (simple plotting)
plt.figure(figsize=(10, 8))
plt.scatter(adata.obs['x'], adata.obs['y'], c=adata.obs['total_counts'], s=10, cmap='viridis')
plt.title('Total counts spatial map')
plt.colorbar()
plt.savefig('results/figures/full_tissue_counts.png')
plt.close()

plt.figure(figsize=(10, 8))
plt.scatter(adata.obs['x'], adata.obs['y'], c=adata.obs['n_genes'], s=10, cmap='plasma')
plt.title('Detected genes spatial map')
plt.colorbar()
plt.savefig('results/figures/full_tissue_genes.png')
plt.close()

print("Spatial QC plots generated.")

# Summary stats
summary = {
    "num_bins": int(adata.shape[0]),
    "num_genes": int(adata.shape[1]),
    "mean_counts_per_bin": float(adata.obs['total_counts'].mean()),
    "mean_n_genes_per_bin": float(adata.obs['n_genes'].mean())
}
with open('results/phase3a_summary.json', 'w') as f:
    json.dump(summary, f, indent=4)
print("Summary saved.")
