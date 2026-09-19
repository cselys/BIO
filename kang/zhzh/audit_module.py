import pandas as pd
import numpy as np
import tifffile
import json
import matplotlib.pyplot as plt
from scipy import stats

class StereoAudit:
    def __init__(self, annotation_file, gem_file, tiff_file):
        self.annot_df = pd.read_csv(annotation_file)
        self.gem_file = gem_file
        self.tiff_file = tiff_file
        self.scale_x, self.scale_y = 1.009, 0.927
        self.trans_x, self.trans_y = 12091.78, -5791.37

    def inspect_annotation(self):
        return {
            "num_cells": len(self.annot_df),
            "unique_cell_type_I": self.annot_df['cell_type_I'].nunique(),
            "unique_cell_type_II": self.annot_df['cell_type_II'].nunique(),
            "X_range": (self.annot_df['X'].min(), self.annot_df['X'].max()),
            "Y_range": (self.annot_df['Y'].min(), self.annot_df['Y'].max()),
            "duplicate_cell_ids": self.annot_df['Unnamed: 0'].duplicated().sum(),
            "missing_values": self.annot_df.isnull().sum().to_dict()
        }

    def inspect_gem(self):
        # Using a sample for efficient inspection
        sample_size = 200000
        xs, ys = [], []
        with open(self.gem_file, 'r') as f:
            f.readline()
            for i, line in enumerate(f):
                if i >= sample_size: break
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    xs.append(float(parts[1]))
                    ys.append(float(parts[2]))
        
        return {
            "X_range": (min(xs), max(xs)),
            "Y_range": (min(ys), max(ys)),
            "sample_size": len(xs)
        }

    def run_audit(self):
        annot_info = self.inspect_annotation()
        gem_info = self.inspect_gem()
        
        summary = {
            "annotation": {k: (int(v) if isinstance(v, (np.int64, np.int32)) else v) for k, v in annot_info.items()},
            "gem": gem_info,
            "transformation": {
                "scale": {"x": float(self.scale_x), "y": float(self.scale_y)},
                "translation": {"x": float(self.trans_x), "y": float(self.trans_y)}
            }
        }
        # Handle missing_values dictionary
        if isinstance(summary["annotation"]["missing_values"], dict):
             summary["annotation"]["missing_values"] = {k: int(v) for k, v in summary["annotation"]["missing_values"].items()}

        with open('results/data_audit_summary.json', 'w') as f:
            json.dump(summary, f, indent=4)
        return summary

# Instantiate and run
auditor = StereoAudit('Normal-4_annotation.csv', 'FP200000489TL_B5.gem', 'FP200000579TR_E3.tif')
summary = auditor.run_audit()
print("Audit complete. Summary saved to results/data_audit_summary.json")
