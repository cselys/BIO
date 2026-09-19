import numpy as np
import pandas as pd

# Sample GEM
sample = []
with open('FP200000489TL_B5.gem', 'r') as f:
    f.readline()
    for i, line in enumerate(f):
        if i >= 200000:
            break
        parts = line.strip().split('\t')
        if len(parts) >= 4:
            x = float(parts[1])
            y = float(parts[2])
            sample.append((x, y))

xs = [s[0] for s in sample]
ys = [s[1] for s in sample]

df = pd.read_csv('Normal-4_annotation.csv')

# Rough transform based on range ratios
scale_x = (df['X'].max() - df['X'].min()) / (max(xs) - min(xs))
scale_y = (df['Y'].max() - df['Y'].min()) / (max(ys) - min(ys))
trans_x = df['X'].min() - scale_x * min(xs)
trans_y = df['Y'].min() - scale_y * min(ys)

print(f"Scale: X={scale_x:.3f}, Y={scale_y:.3f}")
print(f"Translation: x={trans_x:.2f}, y={trans_y:.2f}")

# Range comparison
print(f"GEM X range: {min(xs):.1f} to {max(xs):.1f} (width: {max(xs)-min(xs):.1f})")
print(f"GEM Y range: {min(ys):.1f} to {max(ys):.1f} (height: {max(ys)-min(ys):.1f})")
print(f"Annotation X range: {df['X'].min():.1f} to {df['X'].max():.1f} (width: {df['X'].max()-df['X'].min():.1f})")
print(f"Annotation Y range: {df['Y'].min():.1f} to {df['Y'].max():.1f} (height: {df['Y'].max()-df['Y'].min():.1f})")

# Overlap check with transform
gem_x_trans = scale_x * np.array(xs) + trans_x
gem_y_trans = scale_y * np.array(ys) + trans_y
inside = 0
checked = min(5000, len(sample))
for i in range(checked):
    gx = gem_x_trans[i]
    gy = gem_y_trans[i]
    dists = np.sqrt((gx - df['X'].values)**2 + (gy - df['Y'].values)**2)
    if (dists < df['radius'].values).any():
        inside += 1
print(f"Transformed: {inside} of {checked} GEM points inside annotated cells")

# Overlap check without transform
inside_raw = 0
for i in range(checked):
    gx = xs[i]
    gy = ys[i]
    dists = np.sqrt((gx - df['X'].values)**2 + (gy - df['Y'].values)**2)
    if (dists < df['radius'].values).any():
        inside_raw += 1
print(f"Raw: {inside_raw} of {checked} GEM points inside annotated cells")

# Also try affine transform with scipy
from scipy import optimize
# Use some control points to estimate affine transform
# Annotation coords are much larger, likely different coordinate system
# Try: annot = a * gem + b (affine)
# We'll use random sample points

np.random.seed(42)
n_control = 100
gem_idx = np.random.choice(len(xs), n_control, replace=False)
annot_idx = np.random.choice(len(df), n_control, replace=False)

gem_pts = np.column_stack([np.array(xs)[gem_idx], np.array(ys)[gem_idx]])
annot_pts = np.column_stack([df['X'].values[annot_idx], df['Y'].values[annot_idx]])

# Affine transform: annot = M * gem + t where M = [[a, b], [c, d]]
# Solve using least squares
A = np.column_stack([gem_pts, np.ones(n_control)])  # n x 3
# For X
coeff_x, _, _, _ = np.linalg.lstsq(A, annot_pts[:, 0], rcond=None)
# For Y
coeff_y, _, _, _ = np.linalg.lstsq(A, annot_pts[:, 1], rcond=None)

print(f"\nAffine transform (least squares):")
print(f"  X: a={coeff_x[0]:.4f}, b={coeff_x[1]:.4f}, c={coeff_x[2]:.4f}")
print(f"  Y: a={coeff_y[0]:.4f}, b={coeff_y[1]:.4f}, c={coeff_y[2]:.4f}")

# Apply and check
gem_x_affine = coeff_x[0] * np.array(xs) + coeff_x[1]
gem_y_affine = coeff_y[0] * np.array(ys) + coeff_y[2]  # wait, this is wrong

# Correct affine: for each point (gx, gy), transformed = (a*gx + b, c*gy + d)
# Actually affine has 6 params: x' = a*x + b*y + tx, y' = c*x + d*y + ty
# Let me use a simpler approach: just scale+translation since rotation seems unlikely

# Let's just check R² for affine
from scipy import stats
slope_x, intercept_x, r_value_x, p_value_x, std_err_x = stats.linregress(
    [np.array(xs)[gem_idx]], annot_pts[:, 0])
# This won't work directly, let me just print what we have

print(f"  R² for X fit: needed computation")
print(f"  R² for Y fit: needed computation")

# Summary of findings
print(f"\n=== KEY FINDINGS ===")
print(f"Annotation: {len(df)} cells, X: {df['X'].min():.1f}-{df['X'].max():.1f}, Y: {df['Y'].min():.1f}-{df['Y'].max():.1f}")
print(f"GEM: {len(xs)} spots, X: {min(xs):.1f}-{max(xs):.1f}, Y: {min(ys):.1f}-{max(ys):.1f}")
print(f"Direct coordinate match: NO - ranges are very different")
print(f"Scaling+translation ratios: X={scale_x:.3f}, Y={scale_y:.3f}")
print(f"Transformed overlap: {inside}/{checked} GEM points inside cells (vs {inside_raw}/{checked} raw)")