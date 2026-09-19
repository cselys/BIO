import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def get_cell_type_palette(unique_types, counts_dict=None):
    """Returns a deterministic mapping of cell types to colors."""
    cmap = plt.get_cmap('tab20', 20)
    sorted_types = sorted(unique_types)
    palette = {cell_type: cmap(i) for i, cell_type in enumerate(sorted_types)}
    return palette

def get_legend_handles(palette, counts_dict=None):
    """Creates legend handles, optionally with counts."""
    handles = []
    for cell_type, color in palette.items():
        if counts_dict:
            count = counts_dict.get(cell_type, 0)
            label = f"{cell_type} ({count:,})"
        else:
            label = cell_type
        handles.append(mpatches.Patch(color=color, label=label))
    return handles

def plot_spatial_overlay(ax, data, palette, title, s=0.5, alpha=0.5):
    """Unified plotting function to ensure consistent style."""
    for cell_type, color in palette.items():
        subset = data[data['cell_type_I'] == cell_type]
        ax.scatter(subset['X'], subset['Y'], s=s, c=[color], alpha=alpha, label=cell_type, rasterized=True)
    
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlabel("X (Annotation)")
    ax.set_ylabel("Y (Annotation)")
    # Note: Legend placement is NOT handled here to keep spatial plotting clean
