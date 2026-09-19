import pandas as pd
import numpy as np
from scipy import spatial
import json
import itertools

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
sample_size = 500000 
sample = []
print("Sampling GEM for transform sensitivity...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(f):
        if i >= sample_size: break
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        sample.append((x_gem, y_gem, count))

# Perturbations
scales = [-0.005, 0, 0.005]
trans = [-50, 0, 50]
results = []

print("Running transform sensitivity...")
for ds, dt in itertools.product(scales, trans):
    sc_x = transform['scale_x'] + ds
    sc_y = transform['scale_y'] + ds
    tr_x = transform['translation_x'] + dt
    tr_y = transform['translation_y'] + dt
    
    assigned_spots = 0
    for x_gem, y_gem, count in sample:
        x_annot = sc_x * x_gem + tr_x
        y_annot = sc_y * y_gem + tr_y
        dist, idx = tree.query([x_annot, y_annot])
        if dist <= radii[idx]:
            assigned_spots += 1
            
    results.append({
        "delta_scale": ds,
        "delta_trans": dt,
        "pct_spots_assigned": (assigned_spots / len(sample)) * 100
    })

pd.DataFrame(results).to_csv('results/transformation_sensitivity.csv', index=False)
print("Transformation sensitivity saved.")
