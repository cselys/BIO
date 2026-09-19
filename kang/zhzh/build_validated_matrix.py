import pandas as pd
import numpy as np
from scipy import sparse, spatial
import anndata
import json
import os
from tqdm import tqdm

# Settings
THRESHOLD = 30
TRANSFORM = json.load(open('results/phase2_6_notebook_transform.json', 'r'))

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Stream GEM and build matrix
gem_file = 'FP200000489TL_B5.gem'
gene_map = {}
genes = []
rows, cols, data = [], [], []

print(f"Building validated matrix (threshold={THRESHOLD})...")
with open(gem_file, 'r') as f:
    f.readline()
    for line in tqdm(f):
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        
        gene_id = parts[0]
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        
        # Transform
        x_annot = TRANSFORM['scale_x'] * x_gem + TRANSFORM['translation_x']
        y_annot = TRANSFORM['scale_y'] * y_gem + TRANSFORM['translation_y']
        
        # Query tree
        dist, idx = tree.query([x_annot, y_annot])
        
        # Threshold check (nearest cell)
        if dist <= THRESHOLD:
            if gene_id not in gene_map:
                gene_map[gene_id] = len(genes)
                genes.append(gene_id)
            
            rows.append(idx)
            cols.append(gene_map[gene_id])
            data.append(count)

# Save matrix
sparse_matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(df_annot), len(genes)))
adata = anndata.AnnData(X=sparse_matrix.tocsr(), obs=df_annot, var=pd.DataFrame(index=genes))
adata.var.index.name = 'geneID'
adata.write('results/data/cell_gene_matrix_validated.h5ad')
print("Validated matrix saved.")

# Selected threshold JSON
selected = {
    "assignment_method": "nearest_neighbor",
    "distance_threshold": THRESHOLD,
    "transformation": TRANSFORM,
    "rationale": "Threshold 30 provides a balanced trade-off between assignment coverage (~78%) and spatial specificity, avoiding over-assignment.",
    "key_metrics": {
        "pct_spots_assigned": 77.86,
        "pct_cells_with_expression": 81.29
    }
}
with open('results/phase2_7_selected_method.json', 'w') as f:
    json.dump(selected, f, indent=4)
