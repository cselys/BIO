import pandas as pd
import numpy as np
from scipy import sparse, spatial
import anndata
import json
import os
from tqdm import tqdm

# Load transform
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)

# Prepare to build sparse matrix
# Need map from cell_id to index
cell_ids = df_annot['Unnamed: 0'].values
cell_id_to_idx = {cid: i for i, cid in enumerate(cell_ids)}

# Stream GEM and assign
gem_file = 'FP200000489TL_B5.gem'
all_data = [] # (cell_idx, gene_idx, count)

# Need gene map
gene_to_idx = {}
genes = []

chunk_size = 1000000
total_assigned = 0
total_unassigned = 0
total_midcounts = 0

print("Streaming GEM and assigning points...")
with open(gem_file, 'r') as f:
    f.readline() # header
    for line in tqdm(f):
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        
        gene_id = parts[0]
        x_gem = float(parts[1])
        y_gem = float(parts[2])
        count = int(parts[3])
        total_midcounts += count
        
        # Transform
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        
        # Query tree
        dist, idx = tree.query([x_annot, y_annot])
        
        # Check radius
        if dist <= df_annot.iloc[idx]['radius']:
            # Assign
            if gene_id not in gene_to_idx:
                gene_to_idx[gene_id] = len(genes)
                genes.append(gene_id)
            
            all_data.append((idx, gene_to_idx[gene_id], count))
            total_assigned += count
        else:
            total_unassigned += count

# Build matrix
rows = [x[0] for x in all_data]
cols = [x[1] for x in all_data]
data = [x[2] for x in all_data]
sparse_matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(df_annot), len(genes)))

# Create AnnData
adata = anndata.AnnData(X=sparse_matrix.tocsr(), obs=df_annot, var=pd.DataFrame(index=genes))
adata.var.index.name = 'geneID'
adata.write('results/data/cell_gene_matrix.h5ad')

# Save stats
stats = {
    "total_assigned": total_assigned,
    "total_unassigned": total_unassigned,
    "total_midcounts": total_midcounts,
    "fraction_assigned": total_assigned / total_midcounts if total_midcounts > 0 else 0
}
with open('results/phase2_summary.json', 'w') as f:
    json.dump(stats, f, indent=4)
print("AnnData created and summary saved.")
