import numpy as np
import random
import pandas as pd
from scipy import stats

# Sample GEM with correct parsing
sample = []
with open('FP200000489TL_B5.gem', 'r') as f:
    f.readline()  # skip header
    for i, line in enumerate(f):
        if i >= 200000:
            break
        parts = line.strip().split('\t')
        if len(parts) >= 4:
            gene_id = parts[0]  # keep as string
            x = float(parts[1])
            y = float(parts[2])
            midcount = float(parts[3])
            sample.append((gene_id, x, y, midcount))

xs = [s[1] for s in sample]
ys = [s[2] for s in sample]
mcs = [s[3] for s in sample]
gene_ids = [s[0] for s in sample]

print(f'GEM sample size: {len(sample)}')
print(f'X range: {min(xs)} to {max(xs)}')
print(f'Y range: {min(ys)} to {max(ys)}')
print(f'MIDCounts mean: {np.mean(mcs):.2f}, std: {np.std(mcs):.2f}')

# Mitochondrial gene check
mt_count = sum(1 for g, x, y, mc in sample if g.startswith('MT-') or g.startswith('mt-'))
print(f'MT genes in sample: {mt_count}')

# Linear regression with annotation
df = pd.read_csv('Normal-4_annotation.csv')
annot_sample_ids = random.sample(list(df['Unnamed: 0'].values), min(500, len(df)))
annot_sample = df[df['Unnamed: 0'].isin(annot_sample_ids)]

print(f'\nAnnotation sample: {len(annot_sample)} cells')
print(f'Annotation X range: {annot_sample["X"].min():.2f} to {annot_sample["X"].max():.2f}')
print(f'Annotation Y range: {annot_sample["Y"].min():.2f} to {annot_sample["Y"].max():.2f}')

# Subsample both to same size for regression
n = min(len(xs), len(annot_sample['X'].values))
np.random.seed(42)
annot_sel_idx = np.random.choice(len(annot_sample), n, replace=False)
annot_x_vals = annot_sample['X'].values
annot_y_vals = annot_sample['Y'].values
annot_x_sample = annot_x_vals[annot_sel_idx]
annot_y_sample = annot_y_vals[annot_sel_idx]
gem_x_sample = np.array(xs)[:n]
gem_y_sample = np.array(ys)[:n]

slope_x, intercept_x, r_value_x, p_value_x, std_err_x = stats.linregress(gem_x_sample, annot_x_sample)
slope_y, intercept_y, r_value_y, p_value_y, std_err_y = stats.linregress(gem_y_sample, annot_y_sample)

print(f'\nLinear regression X: slope={slope_x:.4f}, intercept={intercept_x:.4f}, R²={r_value_x**2:.4f}')
print(f'Linear regression Y: slope={slope_y:.4f}, intercept={intercept_y:.4f}, R²={r_value_y**2:.4f}')

# TIFF metadata
import tifffile
import re
with tifffile.TiffFile('FP200000579TR_E3.tif') as tif:
    print(f'\n=== TIFF METADATA ===')
    print('Image description:', tif.description if tif.description else 'None')
    print('Image size:', tif.pages[0].shape)
    print('Dtype:', tif.pages[0].dtype)
    print('Number of pages:', len(tif.pages))
    if tif.ome_metadata:
        print('OME metadata present')
        channels_match = re.search(r'Channels\d*:', tif.ome_metadata)
        if channels_match:
            print('Channels found in OME metadata')
        pixels_match = re.search(r'Pixels\d*:', tif.ome_metadata)
        if pixels_match:
            print('Pixels found in OME metadata')

# Cell-GEM overlap analysis with rough transform
# Try scaling+translation based on range ratios
print(f'\n=== COORDINATE TRANSFORMATION ANALYSIS ===')
print(f'GEM X range: {min(xs):.2f} to {max(xs):.2f}')
print(f'GEM Y range: {min(ys):.2f} to {max(ys):.2f}')
print(f'Annotation X range: {df["X"].min():.2f} to {df["X"].max():.2f}')
print(f'Annotation Y range: {df["Y"].min():.2f} to {df["Y"].max():.2f}')

# Scale factors based on range ratios
scale_x = (df['X'].max() - df['X'].min()) / (max(xs) - min(xs))
scale_y = (df['Y'].max() - df['Y'].min()) / (max(ys) - min(ys))
trans_x = df['X'].min() - scale_x * min(xs)
trans_y = df['Y'].min() - scale_y * min(ys)

print(f'Rough scale+translation: scale_x={scale_x:.4f}, scale_y={scale_y:.4f}')
print(f'  translation_x={trans_x:.2f}, translation_y={trans_y:.2f}')

# Apply transformation and check overlap
gem_x_trans = scale_x * np.array(xs) + trans_x
gem_y_trans = scale_y * np.array(ys) + trans_y

# Check how many transformed GEM points fall inside annotated cells
inside = 0
checked = min(5000, len(gene_ids))
for i in range(checked):
    gx = gem_x_trans[i]
    gy = gem_y_trans[i]
    dists = np.sqrt((gx - df['X'])**2 + (gy - df['Y'])**2)
    if (dists < df['radius']).any():
        inside += 1

print(f'\nAfter rough transform: {inside} of {checked} GEM points fall inside annotated cells')

# Also check without transform
inside_raw = 0
for i in range(checked):
    gx = xs[i]
    gy = ys[i]
    dists = np.sqrt((gx - df['X'])**2 + (gy - df['Y'])**2)
    if (dists < df['radius']).any():
        inside_raw += 1

print(f'Raw coords: {inside_raw} of {checked} GEM points fall inside annotated cells')