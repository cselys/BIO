# Stock Scanner V1.2 — Development Guide

## Installation
1. Navigate to `stock_scanner/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Scanner
- Full scan:
  ```bash
  python run_scanner.py
  ```
- By category:
  ```bash
  python run_scanner.py --category semiconductors
  ```
- Single symbol:
  ```bash
  python run_scanner.py --symbol NVDA
  ```
- With Gemini AI:
  ```bash
  python run_scanner.py --ai
  ```

---

## Running Tests
Run unit tests with pytest:
```bash
python -m pytest
```

---

## Running Historical Evaluation
Execute historical signal evaluation and forward return analysis:
```bash
python run_evaluation.py
```

---

## Configuration (`config/`)
- **`universe.yaml`**: Defines categories, benchmarks, and symbols.
- **`scanner.yaml`**: Configures indicator parameters, scoring weights, entry quality thresholds, and bottom breakout windows.
- *Rule*: Do not hardcode important thresholds in Python code; store them in `scanner.yaml`.

---

## Coding Conventions & Guardrails
1. **No Intraday Engine Dependency**: Keep `stock_scanner` entirely independent.
2. **Causal Calculations**: All indicators must be strictly causal.
3. **No Parameter Overfitting**: Do not tune weights or thresholds arbitrarily against historical results.
4. **Preserve V1.1 Reproducibility**: Maintain compatibility and versioning (`scanner_version = "1.2"`).
