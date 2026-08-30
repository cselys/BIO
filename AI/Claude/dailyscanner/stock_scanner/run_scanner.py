#!/usr/bin/env python3
"""
CLI entry point for stock_scanner.
"""

import argparse
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

from stock_scanner.src.scanner import StockScanner
from stock_scanner.src.reporting.console import display_console_report
from stock_scanner.src.reporting.csv_report import save_csv_report
from stock_scanner.src.reporting.json_report import save_json_report


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Deterministic Daily/Weekly Stock Scanner System")
    parser.add_argument("--category", type=str, help="Scan a specific stock category from universe.yaml")
    parser.add_argument("--symbol", type=str, help="Scan a single stock symbol")
    parser.add_argument("--state", type=str, help="Filter results by state (e.g. STRONG_UPTREND, UPTREND, BOTTOM_FORMING, REVERSAL)")
    parser.add_argument("--top", type=int, help="Display top N results per state")
    parser.add_argument("--ai", action="store_true", help="Enable Google Gemini AI explanations")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    print("Starting Stock Scanner...")
    scanner = StockScanner()

    results = scanner.scan(
        target_category=args.category,
        target_symbol=args.symbol,
        target_state=args.state,
        enable_ai=args.ai,
        top_n=args.top
    )

    if not results:
        print("No scan results generated.")
        return

    # Display console report
    display_console_report(results, top_n=args.top)

    # Save historical reports (CSV and JSON)
    scan_date = datetime.now().strftime("%Y-%m-%d")
    csv_path = save_csv_report(results, output_dir="data/reports", scan_date=scan_date)
    json_path = save_json_report(results, output_dir="data/reports", scan_date=scan_date)

    print(f"Reports saved successfully:")
    print(f" - CSV:  {csv_path}")
    print(f" - JSON: {json_path}")


if __name__ == "__main__":
    main()
