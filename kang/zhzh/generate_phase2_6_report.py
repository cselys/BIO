import json
import pandas as pd

# Load summaries
with open('results/phase2_5_summary.json', 'r') as f:
    phase2_5 = json.load(f)
with open('results/phase2_6_summary.json', 'r') as f:
    dist_stats = json.load(f)
comparison = pd.read_csv('results/phase2_6_comparison.csv')

# Build summary
phase2_6_summary = {
    "nearest_cell_distance_quantiles": dist_stats,
    "comparison": comparison.to_dict(orient='records'),
    "alignment_decision": "ALIGNMENT NEEDS REFINEMENT"
}

with open('results/phase2_6_summary.json', 'w') as f:
    json.dump(phase2_6_summary, f, indent=4)

# Report HTML
report_content = f"""
<!DOCTYPE html>
<html>
<body>
    <h1>Phase 2.6: Alignment Forensics & Mapping Validation</h1>
    <h2>Key Findings</h2>
    <ul>
        <li><strong>Transformation:</strong> The notebook transformation confirms Phase 1/2 results as near-optimal.</li>
        <li><strong>Assignment Discrepancy:</strong> The 25% assignment rate is primarily due to a overly restrictive radius-based assignment. Nearest-neighbor distance distribution shows a large fraction of GEM points are near annotation cells.</li>
        <li><strong>Annotation Nature:</strong> The annotation CSV is clearly a spatial subset of the full tissue section.</li>
    </ul>
    <h2>Summary Table</h2>
    <table border="1">
        <tr><th>Threshold</th><th>Radius Spots</th><th>Nearest Spots</th></tr>
        { "".join([f"<tr><td>{row['threshold']}</td><td>{row['radius_spots']}</td><td>{row['nearest_spots']}</td></tr>" for _, row in comparison.iterrows()]) }
    </table>
    <h2>Final Decision</h2>
    <p><strong>ALIGNMENT NEEDS REFINEMENT</strong></p>
    <p>The coordinate mapping is valid. The cell-by-gene matrix construction should be re-implemented using a more flexible assignment strategy (e.g., nearest-neighbor within a broader threshold) to improve expression recovery, before proceeding to biological analysis.</p>
</body>
</html>
"""

with open('results/phase2_6_report.html', 'w') as f:
    f.write(report_content)
print("Phase 2.6 report generated.")
