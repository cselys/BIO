import pandas as pd
import numpy as np
from scipy import sparse
import anndata
import json
import os
from tqdm import tqdm

# Bin resolution (100x100)
BIN_SIZE = 100

# 1. Stream GEM and bin data
gem_file = 'FP200000489TL_B5.gem'
chunk_size = 5000000

# Need gene map
gene_map = {}
genes = []

# Using dictionary to store binned data: (bin_x, bin_y) -> {gene_idx: count}
# This could be memory intensive if too many bins, but for 100x100 bins on 16000x12000 grid, 
# that's 160x120 = 19200 bins. Should be fine.
bin_data = {} 

print("Streaming GEM and binning...")
with open(gem_file, 'r') as f:
    f.readline()  # header
    for line in tqdm(f):
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        
        gene_id = parts[0]
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        
        if gene_id not in gene_map:
            gene_map[gene_id] = len(genes)
            genes.append(gene_id)
        gene_idx = gene_map[gene_id]
        
        bin_x, bin_y = int(x_gem // BIN_SIZE), int(y_gem // BIN_SIZE)
        bin_id = (bin_x, bin_y)
        
        if bin_id not in bin_data:
            bin_data[bin_id] = {}
        
        bin_data[bin_id][gene_idx] = bin_data[bin_id].get(gene_idx, 0) + count

# Build matrix
bin_ids = list(bin_data.keys())
rows, cols, data = [], [], []
bin_meta = []
for i, b_id in enumerate(bin_ids):
    for g_idx, count in bin_data[b_id].items():
        rows.append(i)
        cols.append(g_idx)
        data.append(count)
    bin_meta.append({'bin_id': i, 'x': b_id[0] * BIN_SIZE, 'y': b_id[1] * BIN_SIZE})

sparse_matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(bin_ids), len(genes)))

# Create AnnData
adata = anndata.AnnData(X=sparse_matrix.tocsr(), obs=pd.DataFrame(bin_meta), var=pd.DataFrame(index=genes))
adata.var.index.name = 'geneID'

# Save
adata.write('results/data/full_tissue_bins.h5ad')
print("Full-tissue AnnData created.")
