import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
from viz_utils import get_cell_type_palette, get_legend_handles, plot_spatial_overlay

# A. Annotation cell centers colored by cell_type_I
df = pd.read_csv('Normal-4_annotation.csv')
# Randomly subsample for faster plotting
df_sub = df.sample(min(10000, len(df)))

unique_types = sorted(df_sub['cell_type_I'].unique())
counts_dict = df_sub['cell_type_I'].value_counts().to_dict()
palette = get_cell_type_palette(unique_types)
handles = get_legend_handles(palette, counts_dict)

fig, ax = plt.subplots(figsize=(14, 10))
plot_spatial_overlay(ax, df_sub, palette, 'Annotation cell centers by cell_type_I', s=2, alpha=0.7)
ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left', ncol=1, fontsize='x-small')
plt.tight_layout()
plt.savefig('results/figures/annot_typeI.png', dpi=300)
plt.close()
print("Plots generated.")
