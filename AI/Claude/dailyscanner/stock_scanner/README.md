# Stock Scanner System (`stock_scanner`)

A deterministic Daily/Weekly stock scanner built in Python 3.11+.

`stock_scanner` is a standalone project designed to download historical market data using `yfinance`, compute causal technical indicators, detect market structure, calculate multi-dimensional scores (Trend, Bottom, Reversal, Setup Quality), classify stocks into defined market states, compute relative strength against market and category benchmarks, and output console, CSV, and JSON reports with optional Google Gemini AI explanations.

---

## Architecture & Design Principles

1. **Deterministic Technical Analysis**: All indicators and scores are strictly mathematical and reproducible.
2. **No Lookahead Bias / Future Data**: All indicators (EMAs, RSI, MACD, ATR, ROC, slopes, swing points) are causal.
3. **Independent Scopes**: Keeps separate scores (`trend_score`, `bottom_score`, `reversal_score`) rather than one generic score.
4. **Gemini as Explanation Only**: Gemini API is optional and never modifies technical scores, indicators, or classifications.
5. **Robust Error Handling**: One bad or delisted ticker will not terminate the entire scan.

---

## Project Structure

```
stock_scanner/
├── config/
│   ├── universe.yaml
│   └── scanner.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── yfinance_loader.py
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── trend.py
│   │   ├── momentum.py
│   │   ├── volatility.py
│   │   ├── volume.py
│   │   └── structure.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── daily.py
│   │   ├── weekly.py
│   │   ├── relative_strength.py
│   │   └── regime.py
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── trend_score.py
│   │   ├── bottom_score.py
│   │   ├── reversal_score.py
│   │   └── setup_quality.py
│   ├── ai/
│   │   ├── __init__.py
│   │   └── gemini.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── console.py
│   │   ├── csv_report.py
│   │   └── json_report.py
│   └── scanner.py
├── tests/
│   ├── test_indicators.py
│   ├── test_scoring.py
│   ├── test_regime.py
│   └── test_yfinance.py
├── requirements.txt
├── .env.example
├── .gitignore
└── run_scanner.py
```

---

## Installation

1. Navigate to the `stock_scanner` directory:
   ```bash
   cd stock_scanner
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Variables

Copy `.env.example` to `.env` if you wish to use Google Gemini AI explanations:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*Note: The scanner works completely without an API key if `--ai` is not specified.*

---

## Universe & Configuration

- **`config/universe.yaml`**: Defines stock categories (semiconductors, technology, energy, financials, small_caps), their category benchmarks (SMH, QQQ, XLE, XLF, IWM), and symbols. Easily customizable.
- **`config/scanner.yaml`**: Configures all indicator parameters, swing lookbacks, scoring weights, and classification thresholds.

---

## CLI Usage

Run the scanner with various command-line options:

```bash
# Run full universe scan
python run_scanner.py

# Scan specific category
python run_scanner.py --category semiconductors

# Scan single symbol
python run_scanner.py --symbol NVDA

# Filter by state
python run_scanner.py --state STRONG_UPTREND

# Limit top N results per state
python run_scanner.py --top 5

# Enable Gemini AI explanations
python run_scanner.py --ai

# Combine filters and AI
python run_scanner.py --category semiconductors --ai --top 10
```

---

## State Classifications

Stocks are classified into:
- `STRONG_UPTREND`
- `UPTREND`
- `EARLY_UPTREND`
- `BOTTOM_FORMING`
- `BOTTOM_BREAKOUT`
- `REVERSAL`
- `REVERSAL_CONFIRMED`
- `NEUTRAL`
- `DOWNTREND`
- `STRONG_DOWNTREND`
- `AVOID`

---

## Output Files

Scan reports are automatically saved under `data/reports/` by date:
- **`data/reports/YYYY-MM-DD.csv`**: Flat CSV report for spreadsheet analysis.
- **`data/reports/YYYY-MM-DD.json`**: Complete machine-readable JSON structure for downstream integration (e.g. options trading engines).

---

## Testing

Run unit tests with `pytest`:
```bash
pytest
```
