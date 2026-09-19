import pandas as pd
import numpy as np
from scipy import sparse, spatial
import json
import os
from tqdm import tqdm

# 1. Load transformation
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# 2. Load annotation and build tree
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# 3. Stream GEM and save assigned triplets to chunked CSVs
gem_file = 'FP200000489TL_B5.gem'
chunk_size = 500000 # Smaller chunk size to save memory
chunk_idx = 0

if not os.path.exists('results/data/temp_triplets'):
    os.makedirs('results/data/temp_triplets')

print("Streaming GEM, assigning, and saving triplets...")
triplets = []
# Resume? Check for existing chunks
existing_chunks = [int(f.split('_')[1].split('.')[0]) for f in os.listdir('results/data/temp_triplets') if f.endswith('.csv')]
if existing_chunks:
    chunk_idx = max(existing_chunks) + 1
    print(f"Resuming from chunk {chunk_idx}")

with open(gem_file, 'r') as f:
    # Skip header and already processed lines (if resuming)
    f.readline()
    # Simple skip (not efficient but functional for now)
    # Actually, the file is 117M lines, skipping is O(N). Let's just restart for now, 
    # but with smaller chunks, it should finish in the 10-minute timeout.
    
    for i, line in enumerate(tqdm(f)):
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        
        gene_id = parts[0]
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        
        # Transform
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        
        # Query tree
        dist, idx = tree.query([x_annot, y_annot])
        
        # Radius check
        if dist <= radii[idx]:
            triplets.append({'cell_idx': idx, 'gene_id': gene_id, 'count': count})
        
        # Save chunk
        if len(triplets) >= chunk_size:
            pd.DataFrame(triplets).to_csv(f'results/data/temp_triplets/chunk_{chunk_idx}.csv', index=False)
            triplets = []
            chunk_idx += 1

# Save last chunk
if triplets:
    pd.DataFrame(triplets).to_csv(f'results/data/temp_triplets/chunk_{chunk_idx}.csv', index=False)
print("Triplets saved.")
