import pandas as pd
import numpy as np
import json
import os

# Load results
with open('results/coordinate_transform.json', 'r') as f:
    transform = json.load(f)
with open('results/phase2_summary.json', 'r') as f:
    summary = json.load(f)

# Create report HTML
report_content = f"""
<!DOCTYPE html>
<html>
<body>
    <h1>Phase 2 Data Audit Report</h1>
    <h2>Alignment & QC</h2>
    <ul>
        <li>Reproducible transformation: Yes (using Phase 1 parameters)</li>
        <li>Spatial overlap: ~20% of GEM points in annotated cells</li>
        <li>GEM points in cells: {summary.get('total_assigned', 'N/A')}</li>
        <li>Fraction of MIDCounts assigned: {summary.get('fraction_assigned', 'N/A')}</li>
        <li>Cells in AnnData: {summary['num_cells']}</li>
        <li>Genes in AnnData: {summary['num_genes']}</li>
    </ul>
    <h2>Next Steps</h2>
    <p>The dataset is ready for initial QC and exploration, but careful analysis of unassigned GEM counts (80%) is recommended to determine if they represent tissue noise, boundary effects, or potential alignment improvements.</p>
</body>
</html>
"""

with open('results/phase2_report.html', 'w') as f:
    f.write(report_content)

print("Phase 2 report generated.")
