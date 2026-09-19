import pandas as pd
import numpy as np
from scipy import spatial
import json
from tqdm import tqdm

# Load transform
with open('results/phase2_6_notebook_transform.json', 'r') as f:
    transform = json.load(f)

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Sample GEM for comparison (smaller sample for speed)
gem_file = 'FP200000489TL_B5.gem'
sample_size = 500000 
sample = []
print("Sampling GEM for comparison...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(f):
        if i >= sample_size: break
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        sample.append((x_annot, y_annot, count))

# Comparison logic
thresholds = [10, 20, 30, 40, 50]
results = []

print("Running assignment comparison...")
for t in thresholds:
    assigned_radius = 0
    assigned_counts_radius = 0
    assigned_nearest = 0
    assigned_counts_nearest = 0
    
    for x, y, c in tqdm(sample):
        dist, idx = tree.query([x, y])
        
        # Radius
        if dist <= radii[idx]:
            assigned_radius += 1
            assigned_counts_radius += c
        
        # Nearest (threshold)
        if dist <= t:
            assigned_nearest += 1
            assigned_counts_nearest += c
            
    results.append({
        "threshold": t,
        "radius_spots": assigned_radius,
        "nearest_spots": assigned_nearest,
        "radius_counts": assigned_counts_radius,
        "nearest_counts": assigned_counts_nearest
    })

pd.DataFrame(results).to_csv('results/phase2_6_comparison.csv', index=False)
print("Comparison saved.")
