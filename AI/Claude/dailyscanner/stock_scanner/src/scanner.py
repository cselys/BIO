"""
Main Stock Scanner orchestrator for stock_scanner V1.2.
Coordinates configuration, data download, analysis, scoring, classification, reporting, and Gemini AI.
"""

import os
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any

from stock_scanner.src.data.yfinance_loader import YFinanceLoader, DataValidationError
from stock_scanner.src.analysis.daily import run_daily_analysis
from stock_scanner.src.analysis.weekly import run_weekly_analysis
from stock_scanner.src.analysis.relative_strength import calculate_relative_strength
from stock_scanner.src.analysis.regime import classify_state, detect_market_regime
from stock_scanner.src.scoring.trend_score import calculate_trend_score
from stock_scanner.src.scoring.bottom_score import calculate_bottom_score
from stock_scanner.src.scoring.reversal_score import calculate_reversal_score
from stock_scanner.src.scoring.entry_quality import calculate_entry_quality
from stock_scanner.src.scoring.candidate_score import calculate_candidate_score
from stock_scanner.src.ai.gemini import GeminiExplainer
from stock_scanner.src.reporting.console import display_console_report
from stock_scanner.src.reporting.csv_report import save_csv_report
from stock_scanner.src.reporting.json_report import save_json_report

logger = logging.getLogger("stock_scanner")


class StockScanner:
    """Orchestrator for the stock_scanner V1.2 system."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config = self._load_yaml(os.path.join(config_dir, "scanner.yaml"))
        self.universe = self._load_yaml(os.path.join(config_dir, "universe.yaml"))
        self.version = self.config.get('scanner_version', '1.2')
        self.loader = YFinanceLoader()
        self.explainer = GeminiExplainer()

    def _load_yaml(self, path: str) -> dict:
        if not os.path.exists(path):
            logger.warning(f"Config file not found at {path}, using empty dict.")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def scan(
        self,
        target_category: Optional[str] = None,
        target_symbol: Optional[str] = None,
        target_state: Optional[str] = None,
        enable_ai: bool = False,
        top_n: Optional[int] = None
    ) -> List[dict]:
        """
        Run scan across universe or filtered subset.
        """
        categories = self.universe.get('categories', {})
        market_benchmarks = self.universe.get('market_benchmarks', ['SPY', 'QQQ'])

        symbols_to_category = {}
        category_benchmarks = {}

        for cat_name, cat_data in categories.items():
            if target_category and cat_name.lower() != target_category.lower():
                continue
            bench = cat_data.get('benchmark', 'QQQ')
            category_benchmarks[cat_name] = bench
            for sym in cat_data.get('symbols', []):
                sym_upper = sym.strip().upper()
                if target_symbol and sym_upper != target_symbol.upper():
                    continue
                symbols_to_category[sym_upper] = cat_name

        if target_symbol and not symbols_to_category:
            sym_upper = target_symbol.strip().upper()
            symbols_to_category[sym_upper] = target_category or 'custom'
            category_benchmarks[target_category or 'custom'] = 'SPY'

        if not symbols_to_category:
            logger.warning("No symbols found matching criteria.")
            return []

        all_symbols = set(symbols_to_category.keys())
        for bench in market_benchmarks:
            all_symbols.add(bench)
        for bench in category_benchmarks.values():
            all_symbols.add(bench)

        logger.info(f"Downloading historical data for {len(all_symbols)} symbols...")
        raw_data = self.loader.download_universe(list(all_symbols))

        spy_df = raw_data.get('SPY') if 'SPY' in raw_data else raw_data.get('QQQ')
        if spy_df is None and raw_data:
            spy_df = list(raw_data.values())[0]

        # Detect market regime from SPY/QQQ
        market_regime_info = detect_market_regime(spy_df)

        results = []

        for symbol, cat_name in symbols_to_category.items():
            if symbol not in raw_data:
                logger.warning(f"Skipping {symbol}: No data downloaded.")
                continue

            df_daily = raw_data[symbol]
            bench_sym = category_benchmarks.get(cat_name, 'SPY')
            df_bench = raw_data.get(bench_sym) if bench_sym in raw_data else spy_df

            try:
                # 1. Daily Analysis
                df_daily_analyzed, daily_indicators = run_daily_analysis(df_daily, self.config)

                # 2. Weekly Analysis
                df_weekly = self.loader.resample_to_weekly(df_daily)
                weekly_indicators = run_weekly_analysis(df_weekly, self.config)

                # 3. Relative Strength
                rs_analysis = calculate_relative_strength(df_daily, df_bench, periods=[20, 60])

                # 4. Market Structure
                structure_analysis = daily_indicators.get('structure', {})

                # 5. Scores
                trend_score, trend_breakdown = calculate_trend_score(
                    weekly_indicators, daily_indicators, structure_analysis, rs_analysis, self.config
                )
                bottom_score, bottom_breakdown = calculate_bottom_score(
                    daily_indicators, structure_analysis, rs_analysis, df_daily, self.config
                )
                reversal_score, reversal_breakdown = calculate_reversal_score(
                    daily_indicators, weekly_indicators, structure_analysis, rs_analysis, self.config
                )
                entry_quality, entry_details = calculate_entry_quality(
                    daily_indicators, structure_analysis, self.config
                )

                # 6. State Classification
                state = classify_state(
                    trend_score, bottom_score, reversal_score,
                    daily_indicators, weekly_indicators, structure_analysis, rs_analysis, self.config
                )

                # 7. Candidate Score
                candidate_score, candidate_breakdown = calculate_candidate_score(
                    trend_score, entry_quality, rs_analysis, state, self.config
                )

                if target_state and state.lower() != target_state.lower():
                    continue

                record = {
                    'scanner_version': self.version,
                    'symbol': symbol,
                    'category': cat_name,
                    'state': state,
                    'candidate_score': candidate_score,
                    'trend_score': trend_score,
                    'entry_quality': entry_quality,
                    'bottom_score': bottom_score,
                    'reversal_score': reversal_score,
                    'market_regime': market_regime_info['regime'],
                    'market_regime_score': market_regime_info['regime_score'],
                    'trend_score_breakdown': trend_breakdown,
                    'bottom_score_breakdown': bottom_breakdown,
                    'reversal_score_breakdown': reversal_breakdown,
                    'entry_quality_details': entry_details,
                    'candidate_score_breakdown': candidate_breakdown,
                    'daily': daily_indicators,
                    'weekly': weekly_indicators,
                    'relative_strength': rs_analysis,
                    'structure': structure_analysis
                }

                if enable_ai and self.explainer.client:
                    logger.info(f"Generating Gemini AI explanation for {symbol}...")
                    explanation = self.explainer.explain_symbol(symbol, cat_name, state, record, record)
                    if explanation:
                        record['ai_explanation'] = explanation.model_dump()

                results.append(record)
                logger.info(f"Scanned {symbol}: State={state}, Candidate={candidate_score}, Trend={trend_score}, EntryQ={entry_quality}")

            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")

        return results
