import pandas as pd
import numpy as np
from scipy import spatial
import json

# Load transformation
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Sample GEM
gem_file = 'FP200000489TL_B5.gem'
sample_size = 1000000 
sample = []
print("Sampling GEM...")
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

# Sensitivity
results = []
for mult in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
    assigned_spots = 0
    assigned_counts = 0
    
    for x, y, c in sample:
        dist, idx = tree.query([x, y])
        if dist <= radii[idx] * mult:
            assigned_spots += 1
            assigned_counts += c
            
    results.append({
        "radius_multiplier": mult,
        "pct_spots_assigned": (assigned_spots / len(sample)) * 100,
        "pct_counts_assigned": (assigned_counts / sum(s[2] for s in sample)) * 100
    })

pd.DataFrame(results).to_csv('results/radius_sensitivity.csv', index=False)
print("Radius sensitivity saved.")
