import json

# Compile summary
with open('results/phase3a_summary.json', 'r') as f:
    summary = json.load(f)

report_content = f"""
<!DOCTYPE html>
<html>
<body>
    <h1>Phase 3A: Full-Tissue Spatial Reconstruction Report</h1>
    <h2>1. Full-Tissue Summary</h2>
    <ul>
        <li>Total spatial bins (100x100 spots): {summary['num_bins']}</li>
        <li>Mean counts per bin: {summary['mean_counts_per_bin']:.1f}</li>
        <li>Mean genes per bin: {summary['mean_n_genes_per_bin']:.1f}</li>
    </ul>
    <h2>2. Comparison with Annotation</h2>
    <p>The annotation is a clear spatial subset of the full tissue section, as shown in the tissue comparison figure.</p>
    <h2>3. Feasibility of Cell-Level Reconstruction</h2>
    <p>Cell-level reconstruction is technically feasible with Stereo-seq, but requires high-quality segmentation (e.g., using DAPI staining if available, which was not used here). Currently, spatial-bin analysis is the most reliable approach with this dataset.</p>
    <h2>4. Recommendations</h2>
    <ul>
        <li>Stereo-seq ecosystem tools like Stereopy or CellBin are recommended if image data is available.</li>
        <li>For this annotation, further tissue segmentation is required to map the full section at single-cell resolution.</li>
    </ul>
    <h2>5. Status</h2>
    <p>The dataset is ready for spatial bin-based analysis, but not for complete single-cell biological analysis.</p>
</body>
</html>
"""

with open('results/phase3a_report.html', 'w') as f:
    f.write(report_content)
print("Phase 3A report generated.")
