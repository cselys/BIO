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

# Sample GEM
gem_file = 'FP200000489TL_B5.gem'
sample_size = 1000000
sample = []
print("Sampling GEM for sensitivity...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(tqdm(f)):
        if i >= sample_size: break
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        sample.append((x_annot, y_annot, count))

# Sensitivity thresholds
thresholds = [10, 15, 20, 25, 30, 40, 50, 75, 100]
results = []

print("Running threshold sensitivity...")
for t in thresholds:
    assigned_spots = 0
    assigned_counts = 0
    cell_counts = {}
    
    for x, y, c in sample:
        dist, idx = tree.query([x, y])
        if dist <= t:
            assigned_spots += 1
            assigned_counts += c
            cell_counts[idx] = cell_counts.get(idx, 0) + c
            
    results.append({
        "threshold": t,
        "pct_spots_assigned": (assigned_spots / len(sample)) * 100,
        "pct_counts_assigned": (assigned_counts / sum(s[2] for s in sample)) * 100,
        "pct_cells_with_expression": (len(cell_counts) / len(df_annot)) * 100,
        "median_counts_per_cell": np.median(list(cell_counts.values())) if cell_counts else 0
    })

pd.DataFrame(results).to_csv('results/phase2_7_threshold_sensitivity.csv', index=False)
print("Sensitivity analysis saved.")
