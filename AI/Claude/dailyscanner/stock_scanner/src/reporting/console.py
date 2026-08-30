"""
Console reporting for stock_scanner V1.2.
Displays formatted sections for each market state, top ranked candidates, and key V1.2 metrics.
"""

import sys


def display_console_report(results: list[dict], top_n: int = None):
    """
    Print formatted console report grouped by state and top candidates by candidate score.
    """
    if not results:
        print("\nNo scan results to display.")
        return

    # 1. Display Top Candidates Ranked by Candidate Score
    sorted_candidates = sorted(results, key=lambda x: x.get('candidate_score', 0), reverse=True)
    top_display = sorted_candidates[:10] if not top_n else sorted_candidates[:top_n]

    print("\n" + "=" * 110)
    print(" " * 38 + f"STOCK SCANNER V1.2 — TOP CANDIDATES")
    print("=" * 110)
    print(f"{'Rank':<5} {'Symbol':<8} {'Cat':<15} {'State':<18} {'CandScore':<10} {'Trend':<7} {'EntryQ':<7} {'RS(20d)':<9} {'Regime':<15}")
    print("-" * 110)

    for idx, r in enumerate(top_display, 1):
        sym = r.get('symbol', '')
        cat = r.get('category', '')
        state = r.get('state', '')
        cand_score = r.get('candidate_score', 0)
        trend = r.get('trend_score', 0)
        entry_q = r.get('entry_quality', r.get('setup_quality', 0))
        rs_20 = r.get('relative_strength', {}).get('rs_20d', 0.0)
        regime = r.get('market_regime', 'NEUTRAL')

        print(f"{idx:<5} {sym:<8} {cat:<15} {state:<18} {cand_score:<10.1f} {trend:<7.1f} {entry_q:<7.1f} {rs_20:<+9.1f}% {regime:<15}")

    # Group by state
    states_order = [
        'STRONG_UPTREND',
        'UPTREND',
        'EARLY_UPTREND',
        'BOTTOM_FORMING',
        'BOTTOM_BREAKOUT',
        'REVERSAL',
        'REVERSAL_CONFIRMED',
        'NEUTRAL',
        'DOWNTREND',
        'STRONG_DOWNTREND',
        'AVOID'
    ]

    grouped = {state: [] for state in states_order}
    for r in results:
        st = r.get('state', 'NEUTRAL')
        if st in grouped:
            grouped[st].append(r)
        else:
            grouped.setdefault('NEUTRAL', []).append(r)

    print("\n" + "=" * 110)
    print(" " * 40 + "STATE BREAKDOWN")
    print("=" * 110)

    for state in states_order:
        items = grouped[state]
        if not items:
            continue

        items = sorted(items, key=lambda x: x.get('candidate_score', 0), reverse=True)
        if top_n:
            items = items[:top_n]

        print(f"\n--- {state} ({len(items)} symbols) ---")
        print(f"{'Symbol':<8} {'Cat':<15} {'CandScore':<10} {'Trend':<7} {'EntryQ':<7} {'Bottom':<7} {'Revers':<7} {'RS(20d)':<9} {'RSI':<6} {'EMA20%':<7}")
        print("-" * 110)

        for r in items:
            sym = r.get('symbol', '')
            cat = r.get('category', '')
            cand_score = r.get('candidate_score', 0)
            t_score = r.get('trend_score', 0)
            entry_q = r.get('entry_quality', 0)
            b_score = r.get('bottom_score', 0)
            r_score = r.get('reversal_score', 0)
            rs_20 = r.get('relative_strength', {}).get('rs_20d', 0.0)
            rsi = r.get('daily', {}).get('rsi', 50.0)
            dist_ema20 = r.get('daily', {}).get('distance_ema20', 0.0)

            print(f"{sym:<8} {cat:<15} {cand_score:<10.1f} {t_score:<7.1f} {entry_q:<7.1f} {b_score:<7.1f} {r_score:<7.1f} {rs_20:<+9.1f}% {rsi:<6.1f} {dist_ema20:<+7.1f}%")

    print("\n" + "=" * 110 + "\n")
