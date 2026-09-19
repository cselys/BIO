import json
import os

# Transformation parameters from Phase 1
transform = {
    "source_coordinate_system": "GEM (pixel)",
    "target_coordinate_system": "Annotation (spatial)",
    "scale_x": 1.009,
    "scale_y": 0.927,
    "translation_x": 12091.78,
    "translation_y": -5791.37,
    "rotation": 0.0,
    "transformation_type": "scaling_and_translation",
    "num_points_used_for_fitting": 100,
    "alignment_metrics_from_phase1": "20% overlap after transform vs 0.3% raw",
    "version": "1.0",
    "timestamp": "2026-09-17"
}

os.makedirs('results', exist_ok=True)
with open('results/coordinate_transform.json', 'w') as f:
    json.dump(transform, f, indent=4)
print("Transformation parameters saved.")
