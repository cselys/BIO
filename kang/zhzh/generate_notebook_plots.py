import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from viz_utils import get_cell_type_palette, get_legend_handles, plot_spatial_overlay

# Load annotation
df_annot = pd.read_csv('Normal-4_annotation.csv')

# Load transform
with open('results/phase2_6_notebook_transform.json', 'r') as f:
    transform = json.load(f)

# GEM sample for tissue background
gem_file = 'FP200000489TL_B5.gem'
sample_x, sample_y = [], []
print("Sampling GEM for overlay...")
with open(gem_file, 'r') as f:
    f.readline()
    for i, line in enumerate(f):
        if i >= 500000: break
        parts = line.strip().split('\t')
        if len(parts) < 3: continue
        # Use notebook transformation
        x_gem, y_gem = float(parts[1]), float(parts[2])
        sample_x.append(1.0114 * x_gem + 12068.51)
        sample_y.append(0.9251 * y_gem - 5758.86)

# Prepare Cell Type Legend
unique_types = sorted(df_annot['cell_type_I'].unique())
counts_dict = df_annot['cell_type_I'].value_counts().to_dict()
palette = get_cell_type_palette(unique_types)
handles = get_legend_handles(palette, counts_dict)

# Plot cell type overlay
fig, ax = plt.subplots(figsize=(14, 12))
# Plot GEM background
ax.scatter(sample_x, sample_y, s=0.05, c='lightgray', alpha=0.1, label='GEM Tissue', rasterized=True)
plot_spatial_overlay(ax, df_annot, palette, 'Annotated Cells by Cell Type I', s=1, alpha=0.7)
ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left', ncol=1, fontsize='x-small')
plt.tight_layout()
plt.savefig('results/figures/phase2_6_celltype_overlay.png', dpi=300)
plt.close()

# Notebook overlay (raw - restore GOOD version)
fig, ax = plt.subplots(figsize=(10, 10))
ax.scatter(sample_x, sample_y, s=0.05, c='lightgray', alpha=0.1, label='GEM Tissue', rasterized=True)
ax.scatter(df_annot['X'], df_annot['Y'], s=0.05, c='red', alpha=0.5, label='Annotated Cells', rasterized=True)
ax.set_title('Notebook Coordinate Transformation Overlay')
ax.set_aspect("equal")
ax.legend(markerscale=10)
plt.tight_layout()
plt.savefig('results/figures/phase2_6_notebook_overlay.png', dpi=300)
plt.close()
print("Plots generated.")
