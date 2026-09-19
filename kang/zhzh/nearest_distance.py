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

# Stream GEM for nearest distance analysis
gem_file = 'FP200000489TL_B5.gem'
distances = []
# Sample 1M points for distance analysis
sample_size = 1000000

print("Calculating nearest-cell distances...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(tqdm(f)):
        if i >= sample_size: break
        parts = line.strip().split('\t')
        if len(parts) < 3: continue
        
        x_gem, y_gem = float(parts[1]), float(parts[2])
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        
        dist, idx = tree.query([x_annot, y_annot])
        distances.append(dist)

# Quantiles
quantiles = np.percentile(distances, [1, 5, 10, 25, 50, 75, 90, 95, 99])
dist_results = {f"{q}%": float(v) for q, v in zip([1, 5, 10, 25, 50, 75, 90, 95, 99], quantiles)}

with open('results/phase2_6_summary.json', 'w') as f:
    json.dump(dist_results, f, indent=4)

# Plot distance distribution
import matplotlib.pyplot as plt
plt.figure()
plt.hist(distances, bins=100)
plt.title('Nearest Cell Distance Distribution')
plt.savefig('results/figures/phase2_6_nearest_cell_distance.png')
plt.close()
print("Analysis complete.")
