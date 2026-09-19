import json
import os

# Notebook transformation (X, Y are annotation coords, x, y are GEM coords)
# gem_x = (X - 12068.51) / 1.0114  => X = gem_x * 1.0114 + 12068.51
# gem_y = (Y + 5758.86) / 0.9251   => Y = gem_y * 0.9251 - 5758.86

transform = {
    "source": "GEM",
    "target": "Annotation",
    "formula_annot_x": "1.0114 * X_gem + 12068.51",
    "formula_annot_y": "0.9251 * Y_gem - 5758.86",
    "scale_x": 1.0114,
    "scale_y": 0.9251,
    "translation_x": 12068.51,
    "translation_y": -5758.86,
    "transformation_type": "scaling_and_translation_from_notebook",
    "timestamp": "2026-09-17"
}

os.makedirs('results', exist_ok=True)
with open('results/phase2_6_notebook_transform.json', 'w') as f:
    json.dump(transform, f, indent=4)
print("Notebook transformation parameters saved.")
