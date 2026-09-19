import pandas as pd
import numpy as np
from scipy import sparse
import anndata
import json
import os
from tqdm import tqdm

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_ids = df_annot['Unnamed: 0'].values
cell_id_to_idx = {cid: i for i, cid in enumerate(cell_ids)}

# Collect all unique genes
gene_to_idx = {}
all_triplets = []

print("Reading triplets and building gene map...")
for chunk_file in tqdm(os.listdir('results/data/temp_triplets')):
    df = pd.read_csv(os.path.join('results/data/temp_triplets', chunk_file))
    for _, row in df.iterrows():
        if row['gene_id'] not in gene_to_idx:
            gene_to_idx[row['gene_id']] = len(gene_to_idx)
        all_triplets.append((row['cell_idx'], gene_to_idx[row['gene_id']], row['count']))

# Build matrix
rows = [x[0] for x in all_triplets]
cols = [x[1] for x in all_triplets]
data = [x[2] for x in all_triplets]
sparse_matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(df_annot), len(gene_to_idx)))

# Create AnnData
genes = list(gene_to_idx.keys())
adata = anndata.AnnData(X=sparse_matrix.tocsr(), obs=df_annot, var=pd.DataFrame(index=genes))
adata.var.index.name = 'geneID'

# Save
adata.write('results/data/cell_gene_matrix.h5ad')
print("AnnData created.")
