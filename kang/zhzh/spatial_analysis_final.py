import anndata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import scanpy as sc

# Load full tissue
adata = anndata.read_h5ad('results/data/full_tissue_bins.h5ad')
df_annot = pd.read_csv('Normal-4_annotation.csv')

# Load transform
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# Overlay comparison
plt.figure(figsize=(10, 8))
plt.scatter(adata.obs['x'], adata.obs['y'], s=1, c='lightgray', label='Full Tissue')
plt.scatter(df_annot['X'], df_annot['Y'], s=1, c='red', alpha=0.5, label='Annotated Subset')
plt.title('Full Tissue vs Annotated Subset')
plt.legend()
plt.savefig('results/figures/tissue_annotation_overlay.png')
plt.close()

# Preliminary Clustering
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata)
sc.pp.pca(adata)
sc.pp.neighbors(adata)
sc.tl.leiden(adata)
sc.tl.umap(adata)

sc.pl.umap(adata, color='leiden', show=False)
plt.savefig('results/figures/full_tissue_umap.png')
plt.close()

# Spatial cluster map
plt.figure(figsize=(10, 8))
plt.scatter(adata.obs['x'], adata.obs['y'], c=adata.obs['leiden'].astype(int), s=5, cmap='tab20')
plt.title('Spatial cluster map')
plt.savefig('results/figures/spatial_cluster_map.png')
plt.close()

print("Clustering and comparison complete.")
