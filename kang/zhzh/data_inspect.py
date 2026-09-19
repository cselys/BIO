import struct
import csv
import json
import os
import numpy as np
import pandas as pd

# 1. Inspect annotation CSV
print("=" * 60)
print("ANNOTATION CSV INSPECTION")
print("=" * 60)

df = pd.read_csv('Normal-4_annotation.csv')
print(f"Number of cells: {len(df)}")
print(f"Unique cell_type_I: {df['cell_type_I'].nunique()}")
print(f"Unique cell_type_II: {df['cell_type_II'].nunique()}")
print(f"Cell type I counts:\n{df['cell_type_I'].value_counts()}")
print(f"Cell type II counts:\n{df['cell_type_II'].value_counts()}")
print(f"X min/max: {df['X'].min():.2f} / {df['X'].max():.2f}")
print(f"Y min/max: {df['Y'].min():.2f} / {df['Y'].max():.2f}")
print(f"Radius stats: mean={df['radius'].mean():.2f}, std={df['radius'].std():.2f}, min={df['radius'].min():.2f}, max={df['radius'].max():.2f}")
print(f"Duplicate cell IDs: {df['cell_id'].duplicated().sum()}")
print(f"Missing values:\n{df.isnull().sum()}")

# 2. Inspect GEM using streaming
print("\n" + "=" * 60)
print("GEM INSPECTION (streaming)")
print("=" * 60)

# GEM format: geneID, x, y, MIDCounts (tab-separated)
gene_ids = []
x_vals = []
y_vals = []
midcounts = []
unique_coords = set()

with open('FP200000489TL_B5.gem', 'r') as f:
    header = f.readline()  # skip header
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 4:
            gene_id = parts[0]
            x = float(parts[1])
            y = float(parts[2])
            midcount = float(parts[3])
            gene_ids.append(gene_id)
            x_vals.append(x)
            y_vals.append(y)
            midcounts.append(midcount)
            unique_coords.add((x, y))

gene_ids_arr = np.array(gene_ids)
x_arr = np.array(x_vals)
y_arr = np.array(y_vals)
midcounts_arr = np.array(midcounts)

print(f"Number of rows: {len(gene_ids)}")
print(f"Unique genes: {len(set(gene_ids))}")
print(f"X min/max: {min(x_arr):.2f} / {max(x_arr):.2f}")
print(f"Y min/max: {min(y_arr):.2f} / {max(y_arr):.2f}")
print(f"Unique spatial coordinates: {len(unique_coords)}")
print(f"Total MIDCounts: {midcounts_arr.sum():.2f}")
print(f"MIDCounts stats: mean={midcounts_arr.mean():.2f}, std={midcounts_arr.std():.2f}, min={midcounts_arr.min():.2f}, max={midcounts_arr.max():.2f}")

# Distribution of MIDCounts (matplotlib-free approach - just compute stats)
midcounts_sorted = np.sort(midcounts_arr)[::-1]
# percentile stats
print(f"MIDCounts percentiles: P25={np.percentile(midcounts_arr, 25):.2f}, P50={np.percentile(midcounts_arr, 50):.2f}, P75={np.percentile(midcounts_arr, 75):.2f}, P90={np.percentile(midcounts_arr, 90):.2f}, P95={np.percentile(midcounts_arr, 95):.2f}")

# Mitochondrial gene fraction
mt_genes = [g for g in set(gene_ids) if g.startswith('MT-') or g.startswith('mt-')]
mt_indices = [gene_ids.index(g) for g in mt_genes if g in gene_ids]
mt_frac = sum(midcounts_arr[mt_indices]) / midcounts_arr.sum() if mt_genes else 0
print(f"Mitochondrial gene fraction: {mt_frac:.4f}")

# 3. Compare coordinate systems
print("\n" + "=" * 60)
print("COORDINATE SYSTEM COMPARISON")
print("=" * 60)

print(f"Annotation X range: {df['X'].min():.2f} to {df['X'].max():.2f}")
print(f"Annotation Y range: {df['Y'].min():.2f} to {df['Y'].max():.2f}")
print(f"GEM X range: {min(x_arr):.2f} to {max(x_arr):.2f}")
print(f"GEM Y range: {min(y_arr):.2f} to {max(y_arr):.2f}")

# Check if coordinates could be directly related
# Annotation X are ~28000 range, Y are ~±2000 range
# GEM X are ~9000 range, Y are ~4500 range
print("\nAnnotation X ~28K, Y ~±2K - likely row/column indices or transformed coordinates")
print(f"GEM X ~9K, Y ~4.5K - likely pixel coordinates")

# 4. Test coordinate transformations
print("\n" + "=" * 60)
print("COORDINATE TRANSFORMATION TESTS")
print("=" * 60)

# Try simple translation/scaling
# Annotation X: ~28600 ± 600, Y: ~-1700 to 2900
# GEM X: ~9056 ± ~200, Y: ~4586 ± ~200
# Ratio: Annotation X / GEM X ≈ 28600/9056 ≈ 3.16
# Annotation Y / GEM Y ≈ ~2000/4586 ≈ 0.44

# Let's compute a rough affine transform
# Using some sample points

# Sample a few GEM points and annotation points for comparison
np.random.seed(42)
n_sample = min(100, len(df), len(gene_ids))
gem_indices = np.random.choice(len(gene_ids), n_sample, replace=False)
annot_indices = np.random.choice(len(df), n_sample, replace=False)

gem_x_sample = np.array([float(x_arr[i]) for i in gem_indices])
gem_y_sample = np.array([float(y_arr[i]) for i in gem_indices])
annot_x_sample = np.array([float(df['X'].iloc[i]) for i in annot_indices])
annot_y_sample = np.array([float(df['Y'].iloc[i]) for i in annot_indices])

# Try scaling + translation
scale_x = np.std(annot_x_sample) / np.std(gem_x_sample) if np.std(gem_x_sample) != 0 else 1
scale_y = np.std(annot_y_sample) / np.std(gem_y_sample) if np.std(gem_y_sample) != 0 else 1
trans_x = np.mean(annot_x_sample) - scale_x * np.mean(gem_x_sample)
trans_y = np.mean(annot_y_sample) - scale_y * np.mean(gem_y_sample)

print(f"Scaling + translation:")
print(f"  scale_x: {scale_x:.4f}, scale_y: {scale_y:.4f}")
print(f"  translation_x: {trans_x:.2f}, translation_y: {trans_y:.2f}")

# Check R² for linear relationship
from scipy import stats
slope_x, intercept_x, r_value_x, p_value_x, std_err_x = stats.linregress(gem_x_sample, annot_x_sample)
slope_y, intercept_y, r_value_y, p_value_y, std_err_y = stats.linregress(gem_y_sample, annot_y_sample)

print(f"\nLinear regression X: slope={slope_x:.4f}, intercept={intercept_x:.4f}, R²={r_value_x**2:.4f}, p={p_value_x:.2e}")
print(f"Linear regression Y: slope={slope_y:.4f}, intercept={intercept_y:.4f}, R²={r_value_y**2:.4f}, p={p_value_y:.2e}")

# 5. TIFF metadata
print("\n" + "=" * 60)
print("TIFF METADATA INSPECTION")
print("=" * 60)

try:
    import tifffile
    with tifffile.TiffFile('FP200000579TR_E3.tif') as tif:
        print(f"Image description: {tif.description if tif.description else 'None'}")
        print(f"Image size: {tif.pages[0].shape}")
        print(f"Dtype: {tif.pages[0].dtype}")
        print(f"Number of pages: {len(tif.pages)}")
        for i, page in enumerate(tif.pages):
            print(f"  Page {i}: shape={page.shape}, dtype={page.dtype}")
        if tif.imagej_description:
            print(f"ImageJ description: {tif.imagej_description}")
        if tif.ome_metadata:
            xml = tif.ome_metadata
            # Extract basic info
            import re
            channels_match = re.search(r'Channels\d*:\s*\[(.*?)\]', xml)
            if channels_match:
                print(f"Channels: {channels_match.group(1)}")
            pixels_match = re.search(r"Pixels.*X=\[(\d+)\], Y=\[(\d+)\]", xml)
            if pixels_match:
                print(f"Pixels: X={pixels_match.group(1)}, Y={pixels_match.group(2)}")
            resolution_match = re.search(r'PhysicalSizeX\\s*:\s*([\d.]+)', xml)
            if resolution_match:
                print(f"Resolution X: {resolution_match.group(1)}")
            resolution_unit_match = re.search(r'PhysicalSizeUnit\\s*:\s*(\w+)', xml)
            if resolution_unit_match:
                print(f"Resolution unit: {resolution_unit_match.group(1)}")
except ImportError:
    print("tifffile not available for full inspection")
    # Fallback: read raw TIFF header
    with open('FP200000579TR_E3.tif', 'rb') as f:
        data = f.read(200)
        print(f"First 200 bytes (hex): {data[:50].hex()}")
except Exception as e:
    print(f"Error reading TIFF: {e}")

# 6. Check GEM vs annotation coordinate alignment
print("\n" + "=" * 60)
print("COORDINATE ALIGNMENT ANALYSIS")
print("=" * 60)

# Check how many GEM points fall within annotation cell boundaries
# using simple circle test (without transformation, so coordinates are in different spaces)
counts_inside = 0
total_checked = min(5000, len(gene_ids))
for i in range(total_checked):
    gx = float(x_arr[i])
    gy = float(y_arr[i])
    dists = np.sqrt((gx - df['X'])**2 + (gy - df['Y'])**2)
    inside_any = (dists < df['radius']).any()
    if inside_any:
        counts_inside += 1

print(f"GEM points checked (first {total_checked}): {total_checked}")
print(f"GEM points falling inside annotated cells (raw coords): {counts_inside}")
print(f"Note: Expected low count since coordinate systems differ")

# Compute rough transformation and re-check
# Apply scaling+translation to GEM coords and check alignment
gem_x_scaled = scale_x * x_arr + trans_x
gem_y_scaled = scale_y * y_arr + trans_y

inside_after_transform = 0
for i in range(min(5000, len(gene_ids))):
    gx = gem_x_scaled[i]
    gy = gem_y_scaled[i]
    dists = np.sqrt((gx - df['X'])**2 + (gy - df['Y'])**2)
    inside_any = (dists < df['radius']).any()
    if inside_any:
        inside_after_transform += 1

print(f"\nAfter scaling+translation transformation:")
print(f"GEM points falling inside annotated cells: {inside_after_transform} out of {total_checked}")

print("\nDone with inspection.")