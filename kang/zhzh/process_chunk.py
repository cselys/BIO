import pandas as pd
import numpy as np
from scipy import sparse, spatial
import anndata
import json
import os
import sys
from tqdm import tqdm

# Settings
THRESHOLD = 30
TRANSFORM = json.load(open('results/coordinate_transform.json', 'r'))
CHUNK_ID = sys.argv[1]

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Stream GEM and build matrix
gem_file = f'split_gem/chunk_{CHUNK_ID}.gem'
gene_map = {}
genes = []
rows, cols, data = [], [], []

print(f"Building matrix for chunk {CHUNK_ID} (threshold={THRESHOLD})...")
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
        
        # Threshold check
        if dist <= THRESHOLD:
            if gene_id not in gene_map:
                gene_map[gene_id] = len(genes)
                genes.append(gene_id)
            
            rows.append(idx)
            cols.append(gene_map[gene_id])
            data.append(count)

# Save intermediate sparse matrix
os.makedirs('results/data/temp_sparse', exist_ok=True)
sparse_matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(df_annot), len(genes)))
sparse.save_npz(f'results/data/temp_sparse/chunk_{CHUNK_ID}.npz', sparse_matrix.tocsr())
with open(f'results/data/temp_sparse/gene_map_{CHUNK_ID}.json', 'w') as f:
    json.dump(gene_map, f)
print(f"Chunk {CHUNK_ID} saved.")
