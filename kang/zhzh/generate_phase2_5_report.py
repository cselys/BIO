import json
import pandas as pd
import numpy as np

# Load summaries
with open('results/phase2_5_summary.json', 'r') as f:
    counts = json.load(f)
radius_sens = pd.read_csv('results/radius_sensitivity.csv')
transform_sens = pd.read_csv('results/transformation_sensitivity.csv')

# Summary
phase2_5_summary = {
    "count_recovery": counts,
    "max_radius_assignment_pct": radius_sens['pct_spots_assigned'].max(),
    "max_transform_assignment_pct": transform_sens['pct_spots_assigned'].max(),
    "alignment_decision": "ALIGNMENT NEEDS REFINEMENT"
}

with open('results/phase2_5_summary.json', 'w') as f:
    json.dump(phase2_5_summary, f, indent=4)

# Report HTML
report_content = f"""
<!DOCTYPE html>
<html>
<body>
    <h1>Phase 2.5: Alignment Forensics & Mapping Validation</h1>
    <h2>1. Assignment Rates</h2>
    <ul>
        <li>GEM spatial coordinates assigned: {counts['assigned_spots']:,} ({counts['pct_spots_assigned']:.1f}%)</li>
        <li>GEM MIDCounts assigned: {counts['assigned_midcounts']:,} ({counts['pct_midcounts_assigned']:.1f}%)</li>
        <li>Annotated cells receiving expression: {counts['cells_with_expression']:,} ({counts['pct_cells_with_expression']:.1f}%)</li>
    </ul>
    <h2>2. Sensitivity Analysis</h2>
    <p>Radius increase shows modest improvements, suggesting assignment limit is not purely radius-dependent.</p>
    <p>Local coordinate transformation perturbations suggest the Phase 1 transformation is already near optimal.</p>
    <h2>3. Forensic Findings</h2>
    <p>The unassigned signal forms a coherent structure, suggesting the current annotation is likely a <strong>subset</strong> of the full tissue.</p>
    <h2>4. Final Decision</h2>
    <p><strong>ALIGNMENT NEEDS REFINEMENT</strong>: While the transformation is consistent, the low assignment rate suggests incomplete segmentation or tissue coverage. Further analysis of unassigned signal is needed before final biological interpretation.</p>
</body>
</html>
"""

with open('results/phase2_5_report.html', 'w') as f:
    f.write(report_content)
print("Phase 2.5 reports generated.")
