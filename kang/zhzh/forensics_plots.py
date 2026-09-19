import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import spatial

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')
cell_centers = df_annot[['X', 'Y']].values
tree = spatial.cKDTree(cell_centers)
radii = df_annot['radius'].values

# Load transformation
import json
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)

# Sample GEM for plotting
gem_file = 'FP200000489TL_B5.gem'
sample_size = 1000000 # Sample size for plotting
assigned_x, assigned_y = [], []
unassigned_x, unassigned_y = [], []
assigned_c, unassigned_c = [], []

print("Streaming GEM for plots...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(f):
        if i >= sample_size: break
        parts = line.strip().split('\t')
        if len(parts) < 4: continue
        
        x_gem, y_gem, count = float(parts[1]), float(parts[2]), int(parts[3])
        x_annot = transform['scale_x'] * x_gem + transform['translation_x']
        y_annot = transform['scale_y'] * y_gem + transform['translation_y']
        
        dist, idx = tree.query([x_annot, y_annot])
        if dist <= radii[idx]:
            assigned_x.append(x_annot)
            assigned_y.append(y_annot)
            assigned_c.append(count)
        else:
            unassigned_x.append(x_annot)
            unassigned_y.append(y_annot)
            unassigned_c.append(count)

# Plotting
def plot_density(x, y, title, filename):
    plt.figure(figsize=(8, 8))
    plt.hist2d(x, y, bins=500, cmap='inferno')
    plt.title(title)
    plt.colorbar()
    plt.savefig(f'results/figures/{filename}')
    plt.close()

plot_density(assigned_x + unassigned_x, assigned_y + unassigned_y, 'All GEM Density', 'forensics_all_gem.png')
plot_density(assigned_x, assigned_y, 'Assigned GEM Density', 'forensics_assigned.png')
plot_density(unassigned_x, unassigned_y, 'Unassigned GEM Density', 'forensics_unassigned.png')

# Plot overlay
plt.figure(figsize=(10, 10))
plt.scatter(unassigned_x[::100], unassigned_y[::100], s=0.1, alpha=0.1, c='red', label='Unassigned')
plt.scatter(assigned_x[::100], assigned_y[::100], s=0.1, alpha=0.1, c='blue', label='Assigned')
plt.scatter(df_annot['X'][::50], df_annot['Y'][::50], s=1, c='black', alpha=0.5, label='Cells')
plt.title('Alignment Overlay')
plt.legend()
plt.savefig('results/figures/phase2_alignment_overlay.png')
plt.close()
print("Plots generated.")
