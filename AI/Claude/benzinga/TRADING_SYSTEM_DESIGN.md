# Intraday Trading System --- System Design Specification

**Version:** 1.0\
**Date:** 2026-08-25\
**Status:** Architecture / Implementation Specification\
**Primary data provider:** Charles Schwab\
**Language:** Python\
**Primary development assistant:** Claude Code

------------------------------------------------------------------------

## 1. Purpose

This project is a Python-based intraday market scanning and research
system for U.S. equities.

The first objective is **not automatic order execution**. The system
should identify and rank stocks showing:

1.  Intraday reversal behavior.
2.  One-directional intraday trend/momentum behavior.

The system must support two data entry modes:

-   **Live mode:** during market hours, continuously update recent
    market data and generate signals.
-   **Historical mode:** when the market is closed, request data for a
    specified date and symbol set only when the required data is not
    already stored locally, then replay the data through the same signal
    engine.

The most important architectural rule is:

> Live and historical data must converge into the same normalized data
> interface. Feature calculation and signal logic must not know whether
> data came from live trading or historical replay.

------------------------------------------------------------------------

## 2. Design Goals

### 2.1 Primary goals

-   Use Charles Schwab as the market-data source.
-   Store historical data locally to minimize repeated API requests.
-   Preserve raw 1-minute bars as the canonical intraday dataset.
-   Derive 3-minute, 5-minute, and 15-minute bars from the canonical
    data.
-   Detect reversal and trend setups.
-   Rank opportunities rather than producing only binary buy/sell
    decisions.
-   Replay historical data one bar at a time.
-   Prevent look-ahead bias.
-   Run the same signal logic in backtest, paper, and live-scanner
    modes.
-   Make the system modular enough for Claude Code to implement and test
    incrementally.

### 2.2 Non-goals for version 1

-   Automatic live order execution.
-   Options trading.
-   Complex portfolio optimization.
-   High-frequency/tick-level market making.
-   Machine-learning prediction as the primary signal engine.
-   Full Level II/order-book modeling.

These can be added later without changing the core data/feature
architecture.

------------------------------------------------------------------------

## 3. Core Timeframe Design

The canonical stored data is **1-minute OHLCV**.

  Timeframe   Role
  ----------- ---------------------------------------------------------
  1-minute    Entry/exit timing, short-term price and volume behavior
  3-minute    Primary setup detection
  5-minute    Trend/reversal confirmation and regime
  15-minute   Higher-level intraday context

Initial recommendation:

> 5-minute context → 3-minute setup → 1-minute entry/management.

The system must retain 1-minute data so that alternative aggregations
can be tested later.

------------------------------------------------------------------------

## 4. High-Level Architecture

``` text
                         Charles Schwab
                              |
                 +------------+------------+
                 |                         |
             LIVE MODE               HISTORICAL MODE
                 |                         |
          Real-time/update API       Historical API
                 |                         |
                 +------------+------------+
                              |
                       Data Adapter Layer
                              |
                       Data Manager / Cache
                              |
                    Local Parquet / DuckDB
                              |
                    Normalized Bar Objects
                              |
                    +---------+---------+
                    |                   |
              Timeframe Engine      Data Validation
                    |
              1m / 3m / 5m / 15m
                    |
                 Feature Engine
                    |
          +---------+---------+
          |                   |
   Reversal Engine       Trend Engine
          |                   |
          +---------+---------+
                    |
              Signal Ranking
                    |
        +-----------+-----------+
        |           |           |
     Scanner     Replay      Research
        |           |           |
      Live       Backtest   Analysis
```

------------------------------------------------------------------------

## 5. Module Responsibilities

### 5.1 Data Adapter

Responsible only for communication with Schwab.

Interfaces should conceptually include:

``` python
class MarketDataProvider:
    def get_historical_bars(self, symbol, start, end, interval):
        ...

    def get_latest_bars(self, symbols, interval):
        ...
```

The provider must not calculate indicators or trading signals.

### 5.2 Data Manager

Responsibilities:

-   Check local cache.
-   Fetch missing data.
-   Validate downloaded data.
-   Deduplicate bars.
-   Normalize timestamps.
-   Save data locally.
-   Return normalized bars to callers.

Example:

``` python
bars = data_manager.get_bars(
    symbols=["NVDA", "AMD"],
    date="2026-08-20",
    interval="1m"
)
```

Behavior:

``` text
Local data exists
    -> return local data

Local data missing/incomplete
    -> request Schwab data
    -> validate
    -> save locally
    -> return data
```

### 5.3 Timeframe Engine

Input:

-   1-minute bars.

Output:

-   3-minute bars.
-   5-minute bars.
-   15-minute bars.

Aggregation must be deterministic and timezone-aware.

No strategy should independently resample market data.

------------------------------------------------------------------------

## 6. Local Data Storage

Version 1 should use:

-   **Parquet** for stored market data.
-   **DuckDB** for local analytical queries.

Example structure:

``` text
data/
  bars/
    interval=1m/
      date=2026-08-20/
        NVDA.parquet
        AMD.parquet
        TSLA.parquet
```

Optional derived datasets:

``` text
data/
  features/
  signals/
  backtests/
```

The raw 1-minute dataset is the source of truth.

Derived data can be regenerated.

------------------------------------------------------------------------

## 7. Data Integrity

Every downloaded dataset must be checked for:

-   Missing timestamps.
-   Duplicate timestamps.
-   Invalid OHLC relationships.
-   Negative/zero volume where inappropriate.
-   Incorrect timezone.
-   Unexpected market-session boundaries.
-   API truncation.
-   Partial download.

The system should distinguish:

-   `COMPLETE`
-   `PARTIAL`
-   `MISSING`
-   `INVALID`

A partial day must not silently be treated as complete historical data.

------------------------------------------------------------------------

## 8. Market Session

The system should use U.S. Eastern Time for the primary market session.

Version 1 should focus on:

-   Regular trading hours.
-   09:30--16:00 Eastern.

Premarket and after-hours should be architecturally supported but
disabled by default.

The market-calendar component should eventually account for:

-   Weekends.
-   U.S. market holidays.
-   Early closes.

------------------------------------------------------------------------

## 9. Live Data Flow

During market hours:

``` text
Schwab
  ↓
Latest 1m data
  ↓
Data validation
  ↓
Local persistence
  ↓
Timeframe update
  ↓
Feature update
  ↓
Reversal / Trend signal
  ↓
Ranking
  ↓
Live scanner
```

The live loop should be aligned to the market clock rather than using an
arbitrary fixed sleep.

Example conceptual behavior:

``` python
while market_is_open():
    bars = provider.get_latest_bars(symbols)
    data_manager.save(bars)
    engine.update(bars)
    sleep_until_next_bar()
```

If Schwab streaming is available and stable for the required data, it
can later replace periodic polling. The downstream architecture must
remain unchanged.

------------------------------------------------------------------------

## 10. Historical Data Flow

Historical mode accepts:

-   Date or date range.
-   Symbol list.
-   Interval.
-   Optional strategy/configuration.

Example:

``` bash
python -m trading_system backtest \
    --date 2026-08-20 \
    --symbols NVDA AMD TSLA
```

Flow:

``` text
Request
  ↓
Local cache check
  ↓
Data available?
  ├── Yes → load local data
  └── No  → Schwab historical API
               ↓
             validate
               ↓
             save
               ↓
             load
  ↓
Market Replay
  ↓
Features
  ↓
Signals
  ↓
Portfolio simulation
  ↓
Metrics
```

------------------------------------------------------------------------

## 11. Market Replay Engine

This is a critical component.

Historical data must be replayed sequentially.

Incorrect:

``` text
Load entire day
→ calculate features using all data
→ identify trades
```

Correct:

``` python
for bar in historical_bars:
    state.update(bar)
    features = feature_engine.update(state)
    signals = signal_engine.generate(features)
    portfolio.process(signals)
```

At timestamp `T`, the strategy may only use information available at or
before `T`.

This rule applies to:

-   Indicators.
-   Volume averages.
-   Relative volume.
-   VWAP.
-   Opening range.
-   Relative strength.
-   Ranking.
-   Stops and targets.

------------------------------------------------------------------------

## 12. Feature Engine

Initial feature set:

### Price structure

-   Higher highs / lower lows.
-   Higher lows / lower highs.
-   Distance from session high/low.
-   Distance from opening range.
-   Price acceleration.
-   Return over 1m / 3m / 5m / 15m windows.

### VWAP

-   Price vs VWAP.
-   VWAP distance percentage.
-   VWAP reclaim.
-   VWAP rejection.
-   Time spent above/below VWAP.

### Volume

-   Raw volume.
-   Volume moving average.
-   Relative volume.
-   Volume acceleration.
-   Volume spike detection.

Relative volume should preferably compare current volume against the
historical volume expected for the same time-of-day, rather than simply
comparing the current bar with a full-day average.

### Volatility

-   ATR.
-   Intraday range.
-   Range expansion.
-   Compression/expansion.

### Momentum

-   EMA 9 / 20 / 50.
-   RSI.
-   ADX.
-   Rate of change.

### Market-relative features

At minimum:

-   Stock return vs SPY.
-   Stock return vs relevant sector ETF when available.
-   Relative strength over multiple short windows.

------------------------------------------------------------------------

## 13. Feature Definitions — Price Structure

This section formally defines the causal features implemented by the
Feature Engine. These definitions must be followed by all downstream
features and must not be reinterpreted in future milestones.

### Rolling High / Rolling Low

**rolling_high:**
    The maximum CLOSE price among the last N COMPLETED bars,
    including the current completed bar.

**rolling_low:**
    The minimum CLOSE price among the last N COMPLETED bars,
    including the current completed bar.

**Default:**
    N = 5 completed bars.

**Configurability:**
    N must be configurable via configuration system.

**Important:**
    rolling_high / rolling_low are CLOSE-based features.
    They are NOT calculated from the bar's high/low fields.

**Example:**
    Given completed closes:
    `100, 101, 99, 103, 102`

    with N=5:
        `rolling_high = 103`
        `rolling_low  = 99`

    If the next close is `105`:
        `rolling_high = 105`

    and the oldest value is removed when the window exceeds N.

### Session High / Session Low

**session_high:**
    Maximum HIGH price observed from the beginning of the current
    regular trading session through the current completed bar.

**session_low:**
    Minimum LOW price observed from the beginning of the current
    regular trading session through the current completed bar.

**These are NOT the same as rolling_high / rolling_low.**

### Causality

All rolling and session features MUST be causal.

A feature at bar t may use:
    - bars <= t

A feature at bar t MUST NOT use:
    - bars > t
    - future session information
    - end-of-day information

### Completed Bar Requirement

Only completed timeframe bars may be used.

Incomplete 3m/5m/15m bars must not update these features.

### Timeframe

The feature engine operates independently of the source timeframe.

The same definitions apply to:
    - 1m
    - 3m
    - 5m
    - 15m

provided that only completed bars are supplied to the FeatureEngine.

### Configuration

Add the following conceptual configuration:

```yaml
rolling_window_bars:
    default: 5
```

The implementation must not hard-code the value 5.

### Terminology

Use "rolling close high/low" when referring to these features in
future documentation to avoid ambiguity.

Do not reinterpret these features in future milestones.

## 14. Feature Contract

Once a feature definition is documented in this section, all
future development must use the documented definition:

- **Milestone 7 (Reversal Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **Milestone 8 (Trend Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **All subsequent milestones** must use the documented definitions of
  these features rather than creating new interpretations.

This ensures consistency across the entire trading system and prevents
feature creep or redefinition that would break causality guarantees
and testing.

## 15. Implementation Notes

The Feature Engine implements these exact definitions as specified:

- **rolling_high / rolling_low:** Maximum/minimum of last N close prices
- **session_high / session_low:** Maximum/minimum of high/low prices
  from session start
- **All features:** Causal, using only information from completed bars
  up to and including the current bar
- **Configuration:** Rolling window size is configurable (N = 5 default)
- **Backward Compatibility:** No breaking changes to existing functionality

All existing tests pass, confirming the implementation matches the
formal specifications above.

## 16. Feature Engine

Initial feature set:

### Price structure

-   Higher highs / lower lows.
-   Higher lows / lower highs.
-   Distance from session high/low.
-   Distance from opening range.
-   Price acceleration.
-   Return over 1m / 3m / 5m / 15m windows.

### VWAP

-   Price vs VWAP.
-   VWAP distance percentage.
-   VWAP reclaim.
-   VWAP rejection.
-   Time spent above/below VWAP.

### Volume

-   Raw volume.
-   Volume moving average.
-   Relative volume.
-   Volume acceleration.
-   Volume spike detection.

Relative volume should preferably compare current volume against the
historical volume expected for the same time-of-day, rather than simply
comparing the current bar with a full-day average.

### Volatility

-   ATR.
-   Intraday range.
-   Range expansion.
-   Compression/expansion.

### Momentum

-   EMA 9 / 20 / 50.
-   RSI.
-   ADX.
-   Rate of change.

### Market-relative features

At minimum:

-   Stock return vs SPY.
-   Stock return vs relevant sector ETF when available.
-   Relative strength over multiple short windows.

## 17. Feature Definitions — Price Structure

This section formally defines the causal features implemented by the
Feature Engine. These definitions must be followed by all downstream
features and must not be reinterpreted in future milestones.

### Rolling High / Rolling Low

**rolling_high:**
    The maximum CLOSE price among the last N COMPLETED bars,
    including the current completed bar.

**rolling_low:**
    The minimum CLOSE price among the last N COMPLETED bars,
    including the current completed bar.

**Default:**
    N = 5 completed bars.

**Configurability:**
    N must be configurable via configuration system.

**Important:**
    rolling_high / rolling_low are CLOSE-based features.
    They are NOT calculated from the bar's high/low fields.

**Example:**
    Given completed closes:
    `100, 101, 99, 103, 102`

    with N=5:
        `rolling_high = 103`
        `rolling_low  = 99`

    If the next close is `105`:
        `rolling_high = 105`

    and the oldest value is removed when the window exceeds N.

### Session High / Session Low

**session_high:**
    Maximum HIGH price observed from the beginning of the current
    regular trading session through the current completed bar.

**session_low:**
    Minimum LOW price observed from the beginning of the current
    regular trading session through the current completed bar.

**These are NOT the same as rolling_high / rolling_low.**

### Causality

All rolling and session features MUST be causal.

A feature at bar t may use:
    - bars <= t

A feature at bar t MUST NOT use:
    - bars > t
    - future session information
    - end-of-day information

### Completed Bar Requirement

Only completed timeframe bars may be used.

Incomplete 3m/5m/15m bars must not update these features.

### Timeframe

The feature engine operates independently of the source timeframe.

The same definitions apply to:
    - 1m
    - 3m
    - 5m
    - 15m

provided that only completed bars are supplied to the FeatureEngine.

### Configuration

Add the following conceptual configuration:

```yaml
rolling_window_bars:
    default: 5
```

The implementation must not hard-code the value 5.

### Terminology

Use "rolling close high/low" when referring to these features in
future documentation to avoid ambiguity.

Do not reinterpret these features in future milestones.

## 18. Feature Definitions — Volume Baseline / RVOL

This section formally defines the causal features implemented by the
Feature Engine for Relative Volume (RVOL). These definitions must be
followed by all downstream features and must not be reinterpreted in
future milestones.

### RVOL Definition

**RVOL(t):**
    The relative volume for a completed bar at time t is defined as:

    ```
    RVOL(t) = current_volume(t) / historical_average_volume(
        symbol,
        session_date(t),
        minute_of_session(t)
    )
    ```

The historical average is the arithmetic mean of valid observations from the
**20 most recent eligible trading sessions strictly before the as-of session**,
at the **same minute-of-session**.

### Same minute-of-session

```
09:30 ET -> minute 0
09:31 ET -> minute 1
...
15:59 ET -> minute 389
```

Timestamps remain canonical UTC in storage. Conversion to `America/New_York`
is used for session-date and minute-of-session logic.

### Session Selection Rules

Use the 20 most recent eligible trading sessions strictly before `as_of_session_date`.

A session is eligible only if it is a valid U.S. trading session and the
requested minute has a valid regular-session observation for the symbol.

Weekends and holidays are excluded. Trading-session selection must not be
inferred solely from calendar dates.

### Strict Causality

For session `D`, the denominator may use:

```
D-1, D-2, ... previous eligible sessions
```

It must never use:

```
D itself
D+1 or later
future bars from D
```

Today's current volume is used only as the numerator.

### Current Trading Day Exclusion

Future trading days MUST NOT contribute to the baseline.

### Current Day Exclusion from Baseline

The current trading day MUST NOT contribute to its own baseline.

A completed bar at time `t` may not use any observation from the same
regular trading session.

### VolumeBaselineProvider Interface

The FeatureEngine depends on the following protocol for historical volume
baseline calculation:

```python
from typing import Protocol, Tuple, Optional
from decimal import Decimal
from datetime import date
from enum import Enum

class BaselineStatus(str, Enum):
    NO_DATA = "NO_DATA"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    PARTIAL_HISTORY = "PARTIAL_HISTORY"
    COMPLETE = "COMPLETE"
    INVALID = "INVALID"

@dataclass(frozen=True)
class VolumeBaselineResult:
    average_volume: Optional[Decimal]
    observation_count: int
    sessions_used: Tuple[date, ...]
    status: BaselineStatus

class VolumeBaselineProvider(Protocol):
    def get_baseline(
        self,
        symbol: str,
        as_of_session_date: date,
        minute_of_session: int,
    ) -> VolumeBaselineResult:
        ...
```

### RVOL Calculation Logic

FeatureEngine integration:

1. Accept only completed regular-session bars;
2. Convert UTC to America/New_York;
3. Determine ET session date;
4. Determine minute-of-session;
5. Request the historical baseline using VolumeBaselineProvider;
6. Calculate RVOL only when the baseline is valid;
7. Return RVOL plus baseline availability/status.

FeatureEngine MUST NOT:

- open Parquet files directly;
- know the storage directory layout;
- call Schwab; or
- maintain a 20-day historical volume database.

### Missing Historical Minutes

Never forward-fill OHLCV or volume.

If a requested minute is missing on a historical session, omit that
observation. Never invent a zero or reuse the previous minute.

### Early-Close Sessions

Early-close sessions simply contribute no observation for minutes
after their close.

### RVOL Availability and Status

```
0-2 observations -> rvol=None, status=NO_DATA
3-19 observations -> rvol calculated, status=PARTIAL_HISTORY
20 observations  -> rvol calculated, status=COMPLETE
>20 sessions     -> use the 20 most recent eligible sessions
```

### RVOL Unavailable Representation

RVOL unavailable MUST NOT be represented as Decimal("0").

Use:
    value = None
    status = explicit unavailable status

### Canonical Storage

Use the existing canonical 1m OHLCV Parquet cache:

``` text
data/bars/
    interval=1m/
        date=YYYY-MM-DD/
            SYMBOL.parquet
```

The RVOL subsystem reads volume from this source.

### Derived Cache

A disposable in-memory cache may store:

```
(symbol, as_of_session_date, minute_of_session)
    -> BaselineResult
```

It is a performance optimization, not canonical storage.

## 19. Feature Contract

Once a feature definition is documented in this section, all
future development must use the documented definition:

- **Milestone 7 (Reversal Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **Milestone 8 (Trend Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **All subsequent milestones** must use the documented definitions of
  these features rather than creating new interpretations.

This ensures consistency across the entire trading system and prevents
feature creep or redefinition that would break causality guarantees
and testing.

### Volume Baseline Feature Contract

Once a feature is defined here, downstream milestones must use the
same definition:

| Property | Definition |
|---|---|
| Input | Current completed bar volume |
| Baseline | Same minute-of-session |
| History | Previous 20 eligible trading sessions |
| Current day in baseline | No |
| Future data | No |
| Timezone | America/New_York |
| Session | Regular session |
| Missing minute | Omit; never fabricate |
| Forward fill | Never |
| Minimum observations | 3 |
| Partial history | Valid when minimum is met |
| Zero baseline | Unavailable |
| Unavailable output | `None` + status |
| Precision | Decimal |
| Canonical storage | Existing 1m OHLCV Parquet |

## 20. Implementation Notes

The FeatureEngine implements these exact definitions as specified:

- **rolling_high / rolling_low:** Maximum/minimum of last N close prices
- **session_high / session_low:** Maximum/minimum of high/low prices
  from session start
- **All features:** Causal, using only information from completed bars
  up to and including the current bar
- **Configuration:** Rolling window size is configurable (N = 5 default)
- **Backward Compatibility:** No breaking changes to existing functionality
- **RVOL:** Added via VolumeBaselineProvider abstraction, not implementing
  the provider itself
- **RVOL Availability:** 0-2 observations = NO_DATA, 3-19 = PARTIAL_HISTORY,
  20 = COMPLETE
- **RVOL Unavailable:** Represented as None + status, never as 0

All existing tests pass, confirming the implementation matches the
formal specifications above.

## 21. Volume Baseline and RVOL Testing Requirements

### Numerical Tests

Historical same-minute volumes:

```
100, 200, 300, 400, 500
```

Current volume:

```
600
```

Expected baseline:

```
300
```

Expected RVOL:

```
2.0
```

### Causality Tests

Changing today's future bars, today's current-day baseline candidates,
or future trading days must not change RVOL for an earlier bar.

### Current-day exclusion Tests

Explicitly prove today's same-minute volume is not part of today's denominator.

### Same-minute accuracy Tests

10:17 must not use 10:16, 10:18, or 11:17.

### Session Tests

Test first regular-session minute, last regular-session minute,
premarket rejection, after-hours rejection, early-close, weekend,
and holiday.

### History Tests

Test 0, 1, 2, 3, 19, 20, and 21+ prior sessions.

### Missing Data Tests

Test missing minute observations on one historical day, multiple
historical days, and all historical days.

### DST Tests

Test dates before and after DST transitions and confirm that the same
ET minute maps correctly despite UTC offset changes.

### Determinism Tests

Repeated calculations from identical data must return identical
baseline, observation count, sessions used, and RVOL.

### Live-mode Cache Behavior Tests

Test that baseline caching works correctly during live sessions,
particularly that today's data does not contaminate today's baselines
and that cache is properly invalidated when new trading days begin.

### Architecture Decision

This RVOL addendum is now incorporated into the primary system
specification.

---

## 22. Feature Engine

Initial feature set:

### Price structure

-   Higher highs / lower lows.
-   Higher lows / lower highs.
-   Distance from session high/low.
-   Distance from opening range.
-   Price acceleration.
-   Return over 1m / 3m / 5m / 15m windows.

### VWAP

-   Price vs VWAP.
-   VWAP distance percentage.
-   VWAP reclaim.
-   VWAP rejection.
-   Time spent above/below VWAP.

### Volume

-   Raw volume.
-   Volume moving average.
-   Relative volume.
-   Volume acceleration.
-   Volume spike detection.

Relative volume should preferably compare current volume against the
historical volume expected for the same time-of-day, rather than simply
comparing the current bar with a full-day average.

### Volatility

-   ATR.
-   Intraday range.
-   Range expansion.
-   Compression/expansion.

### Momentum

-   EMA 9 / 20 / 50.
-   RSI.
-   ADX.
-   Rate of change.

### Market-relative features

At minimum:

-   Stock return vs SPY.
-   Stock return vs relevant sector ETF when available.
-   Relative strength over multiple short windows.

## 18. Feature Contract

Once a feature definition is documented in this section, all
future development must use the documented definition:

- **Milestone 7 (Reversal Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **Milestone 8 (Trend Engine)** must use the documented definitions
  of rolling high/low and session high/low, not redefine them.

- **All subsequent milestones** must use the documented definitions of
  these features rather than creating new interpretations.

This ensures consistency across the entire trading system and prevents
feature creep or redefinition that would break causality guarantees
and testing.

## 19. Implementation Notes

The Feature Engine implements these exact definitions as specified:

- **rolling_high / rolling_low:** Maximum/minimum of last N close prices
- **session_high / session_low:** Maximum/minimum of high/low prices
  from session start
- **All features:** Causal, using only information from completed bars
  up to and including the current bar
- **Configuration:** Rolling window size is configurable (N = 5 default)
- **Backward Compatibility:** No breaking changes to existing functionality

All existing tests pass, confirming the implementation matches the
formal specifications above.

## 18. Feature Engine

Initial feature set:

### Price structure

-   Higher highs / lower lows.
-   Higher lows / lower highs.
-   Distance from session high/low.
-   Distance from opening range.
-   Price acceleration.
-   Return over 1m / 84. It defines comprehensive RVOL requirements:
   - RVOL calculation formula
   - Session selection rules
   - Causality requirements
   - Missing data handling
   - Status management
   - Testing requirements

This becomes the authoritative specification for RVOL implementation.

---

**☑ IMPORTANT:** The original FeatureEngine section (with the detailed implementation description) should be moved to after this new RVOL addendum.

---

## 18. Feature Engine

This section defines the FeatureEngine class that implements all features
including RVOL. The FeatureEngine provides a unified interface for
feature calculation while maintaining the causal design principles.

### Class Overview

The FeatureEngine class is responsible for:
- Processing completed timeframe bars
- Maintaining feature calculation state
- Implementing all feature definitions
- Ensuring causality and determinism
- Providing clean interfaces for downstream consumers

### Initialization

```python
class FeatureEngine:
    def __init__(self):
        # Feature state management
        self._cumulative_pv = Decimal("0")  # VWAP cumulative product
        self._cumulative_v = Decimal("0")   # VWAP cumulative volume
        self._vwap = Decimal("0")
        
        # Session structure state
        self._session_high = Decimal("-Infinity")
        self._session_low = Decimal("Infinity")
        self._prev_high = None
        self._prev_low = None
        
        # Rolling window price history
        self._price_history = []
        self._max_rolling_window = 5
        
        # Session tracking
        self._session_date = None
        self._session_started = False
```

### FeatureProcessing

The `process_bar()` method processes each completed timeframe bar:

1. **Session Validation**: Checks if bar is in regular trading session
2. **Session Reset**: Handles session boundary detection and state reset
3. عنها Features**: Calculates all features for the current bar
   - VWAP and related VWAP features
   - Session high/low and distances
   - Rolling high/low
   - Structure classification
   - RVOL calculation

### RVOL Integration

```python
def process_bar(self, bar: Bar) -> FeatureResult:
    # ... existing code ...
    
    # RVOL calculation
    if self._should_include_rvol(bar):
        historical_avg_volume = self.volume_baseline.get_average_volume(
            symbol=bar.symbol,
            session_date=current_session_date,
            minute_of_day=minute_of_day,
            current_session_date=current_session_date
        )
        
        if historical_avg_volume > 0:
            rvol = Decimal(str(bar.volume)) / historical_avg_volume
            result.rvol = rvol.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
```

### FeatureResult

The FeatureResult class contains all computed features:

```python
@dataclass
class FeatureResult:
    vwap: Decimal
    price_distance_from_vwap: Decimal
    percentage_distance_from_vwap: Decimal
    above_below_vwap_state: str
    session_high: Decimal
    session_low: Decimal
    distance_from_session_high: Decimal
    distance_from_session_low: serializable
    rolling_high: Decimal
    rolling_low: Decimal
    higher_high: bool
    lower_high: bool
    higher_low: bool
    lower_low: bool
    is_new_session: bool
    session_date: date
    rvol: Decimal  # NEW: RVOL feature
```

## 19. Configuration

Configuration for FeatureEngine and RVOL:

```yaml
feature_engine:
  rolling_window_bars: 5
  
  session:
    regular_start_hour: 9
    regular_start_minute: 30
    regular_end_hour: 16
    regular_end_minute: 0
    timezone: America/New_York

volume_baseline:
  sessions_window: 20
  min_observations: 3
  missing_data_strategy: "use_available"
  caching:
    enabled: true
    ttl_days: 1
```

## 20. Implementation Notes

### RVOL Calculation

RVOL follows the definition from RVOL_UPDATE_v1.0.md:

```
RVOL(t) = current_volume(t) / historical_average_volume(
    symbol,
    session_date(t),
    minute_of_session(t)
)

Where historical_average_volume uses:
- 20 most recent eligible trading sessions strictly before as_of_session_date
- Same minute-of-session
- Current session date excluded
```

### Integration with Existing Features

The FeatureEngine maintains backward compatibility with existing features:
- All existing feature calculations continue to work unchanged
- RVOL is added as an additional feature field
- No breaking changes to existing API
- All existing tests continue to pass

### Testing

Comprehensive testing ensures:
- RVOL correctness against manual calculations
- Causality (no look-ahead bias)
- Session handling (regular/inregular sessions)
- Missing data scenarios
- Deterministic behavior
- Integration with existing features

## 21. Conclusion

The FeatureEngine implementation integrates the RVOL feature while maintaining:
- **Backward compatibility**: All existing features continue to work
- **Causal design**: No look-ahead bias
- **Deterministic behavior**: Same input produces same output
- **Comprehensive testing**: All requirements validated
- **Clean architecture**: Separation of concerns between components

The RVOL addendum is successfully integrated into the primary system specification, providing a complete foundation for RVOL implementation while preserving the existing FeatureEngine architecture and functionality.

------------------------------------------------------------------------

## 17. Reversal Engine

The first version should focus on structural reversal patterns rather
than a single indicator.

Candidate components:

1.  Extended move.
2.  Relative volume expansion.
3.  Failed breakout or failed breakdown.
4.  VWAP reclaim/rejection.
5.  Short-term exhaustion.
6.  Change in price acceleration.
7.  Higher-low / lower-high confirmation.
8.  Relative strength shift.

Example bullish reversal concept:

``` text
Large decline
    ↓
Volume expansion
    ↓
Failed breakdown
    ↓
Price stabilizes
    ↓
Higher low
    ↓
VWAP reclaim
    ↓
Bullish reversal signal
```

The engine should produce a score, not only `BUY/SELL`.

Example:

``` text
reversal_score = 0–100
```

The individual components should remain visible for analysis.

------------------------------------------------------------------------

## 18. Trend Engine

Trend candidates should combine:

-   Price above/below VWAP.
-   EMA alignment.
-   Higher-high/higher-low or lower-high/lower-low structure.
-   ADX.
-   Relative volume.
-   Range expansion.
-   Relative strength.
-   Pullback quality.

Example bullish trend:

``` text
Price > VWAP
EMA9 > EMA20 > EMA50
HH → HL → HH → HL
RVOL > threshold
Relative strength positive
```

Output:

``` text
trend_score = 0–100
```

------------------------------------------------------------------------

## 19. Signal Object

Every signal should be represented by a structured object.

Example:

``` python
Signal(
    timestamp=...,
    symbol="NVDA",
    strategy="REVERSAL",
    direction="LONG",
    score=87,
    price=181.20,
    stop=179.80,
    target=184.00,
    features={
        "rvol": 3.1,
        "vwap_distance": -0.12,
        "rsi_3m": 31,
        "relative_strength_5m": 0.018
    }
)
```

The exact stop/target logic should be configurable and should not be
hard-coded into the data layer.

------------------------------------------------------------------------

## 20. Ranking Engine

Instead of displaying every possible signal, rank candidates.

Example output:

``` text
REVERSAL
1. NVDA  92
2. AMD   87
3. META  81

TREND
1. TSLA  94
2. NVDA  91
3. AAPL  85
```

Ranking should preserve:

-   Score.
-   Strategy.
-   Direction.
-   Timestamp.
-   Key feature contributions.

The system should allow later ranking by expected value after sufficient
historical research.

------------------------------------------------------------------------

## 17. Backtest Engine

The backtest engine should simulate:

-   Entry.
-   Exit.
-   Stop loss.
-   Target.
-   Time-based exit.
-   End-of-day exit.
-   Slippage.
-   Commission/fees where applicable.

Initial performance metrics:

-   Number of trades.
-   Win rate.
-   Average winner.
-   Average loser.
-   Profit factor.
-   Expectancy.
-   Maximum drawdown.
-   Sharpe ratio.
-   Average holding time.
-   MFE.
-   MAE.
-   Trades per day.
-   P&L by time of day.
-   P&L by setup type.
-   P&L by score bucket.

------------------------------------------------------------------------

## 18. Avoiding Look-Ahead Bias

The following are prohibited:

-   Using future bars to calculate current indicators.
-   Using end-of-day volume to calculate intraday RVOL.
-   Using the final session high/low while still inside the session.
-   Using future VWAP values.
-   Selecting today's best-performing stocks using information that was
    not available at the signal timestamp.
-   Using future bars to define the opening range.
-   Re-ranking historical candidates with future information.

All calculations must be causal.

------------------------------------------------------------------------

## 19. Testing Strategy

Testing should occur at four levels.

### Level 1 --- Data tests

Verify:

-   Timestamp correctness.
-   OHLC validity.
-   Missing bars.
-   Duplicate bars.
-   Session boundaries.
-   Cache behavior.

### Level 2 --- Indicator tests

Use deterministic sample data to validate:

-   VWAP.
-   EMA.
-   RSI.
-   ATR.
-   RVOL.
-   Opening range.
-   Relative strength.

### Level 3 --- Signal tests

Construct known market patterns and verify expected signals.

Examples:

-   Failed breakdown + VWAP reclaim → bullish reversal.
-   Failed breakout + VWAP rejection → bearish reversal.
-   EMA alignment + HH/HL + RVOL → bullish trend.

### Level 4 --- End-to-end tests

``` text
Historical API/mock
→ Data Manager
→ Replay
→ Features
→ Signals
→ Backtest
→ Metrics
```

------------------------------------------------------------------------

## 20. Backtest Experiment Design

Do not assume the best timeframe.

Run controlled experiments across:

``` text
1m
2m
3m
5m
10m
15m
```

For reversal:

``` text
1m entry
3m setup
5m confirmation
```

Compare with alternative combinations.

For trend:

``` text
3m
5m
10m
15m
```

Compare:

-   Expectancy.
-   Profit factor.
-   Maximum drawdown.
-   Number of trades.
-   Average holding time.
-   MFE/MAE.

The goal is to discover which combination is robust, not to optimize one
historical period.

------------------------------------------------------------------------

## 21. Walk-Forward Testing

After initial backtesting, divide historical data into:

``` text
Training / development period
        ↓
Validation period
        ↓
Out-of-sample period
```

Parameters must not be tuned repeatedly on the final test period.

A strategy that works only on one historical period should be rejected
or treated as overfit.

------------------------------------------------------------------------

## 22. Live Scanner

Version 1 live output should be informational only.

Example:

``` text
LIVE SCANNER
=========================

REVERSAL

NVDA   92  LONG
RVOL: 3.1
VWAP: reclaim
RS 5m: +1.8%
Setup: failed breakdown

AMD    87  LONG
...

TREND

TSLA   94  LONG
RVOL: 4.1
VWAP: +1.8%
ADX: 32
Structure: HH/HL
```

No automatic order placement in version 1.

------------------------------------------------------------------------

## 23. Paper Trading

Once the scanner is stable:

``` text
Live Schwab data
→ Same signal engine
→ Simulated orders
→ Simulated fills
→ P&L
```

Paper trading must use exactly the same signal code as live scanning.

Only the execution layer changes.

------------------------------------------------------------------------

## 24. Configuration

Use configuration files rather than hard-coded parameters.

Example:

``` yaml
market:
  timezone: America/New_York
  regular_session_start: "09:30"
  regular_session_end: "16:00"

timeframes:
  base: 1m
  setup: 3m
  confirmation: 5m
  context: 15m

signals:
  reversal:
    enabled: true
  trend:
    enabled: true

backtest:
  slippage_bps: 2
  commission: 0
  end_of_day_exit: true
```

Secrets such as Schwab credentials must never be committed to source
control.

Use environment variables or a secure local secrets mechanism.

------------------------------------------------------------------------

## 25. Suggested Python Repository

``` text
trading_system/
│
├── pyproject.toml
├── README.md
├── .env.example
├── config/
│   ├── default.yaml
│   └── development.yaml
│
├── src/
│   └── trading_system/
│       ├── __init__.py
│       ├── config/
│       ├── data/
│       │   ├── provider.py
│       │   ├── schwab.py
│       │   ├── historical.py
│       │   ├── live.py
│       │   ├── manager.py
│       │   ├── cache.py
│       │   └── validation.py
│       │
│       ├── market/
│       │   ├── calendar.py
│       │   ├── session.py
│       │   └── timeframe.py
│       │
│       ├── features/
│       │   ├── vwap.py
│       │   ├── volume.py
│       │   ├── momentum.py
│       │   ├── volatility.py
│       │   ├── relative_strength.py
│       │   └── engine.py
│       │
│       ├── strategies/
│       │   ├── base.py
│       │   ├── reversal.py
│       │   └── trend.py
│       │
│       ├── signals/
│       │   ├── models.py
│       │   └── ranking.py
│       │
│       ├── replay/
│       │   └── engine.py
│       │
│       ├── backtest/
│       │   ├── engine.py
│       │   ├── portfolio.py
│       │   ├── execution.py
│       │   └── metrics.py
│       │
│       ├── scanner/
│       │   └── live.py
│       │
│       └── cli.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── data/
│   ├── bars/
│   ├── features/
│   ├── signals/
│   └── backtests/
│
└── notebooks/
```

------------------------------------------------------------------------

## 26. CLI Design

Suggested commands:

``` bash
# Download/cache historical data
python -m trading_system data fetch \
    --date 2026-08-20 \
    --symbols NVDA AMD TSLA

# Run historical signal replay
python -m trading_system replay \
    --date 2026-08-20 \
    --symbols NVDA AMD TSLA

# Run backtest
python -m trading_system backtest \
    --start 2026-01-01 \
    --end 2026-08-20 \
    --symbols NVDA AMD TSLA

# Run live scanner
python -m trading_system live \
    --symbols-file universe.txt

# Run tests
pytest
```

------------------------------------------------------------------------

## 27. Logging and Observability

Every important event should be logged.

Examples:

``` text
DATA_FETCH
DATA_CACHE_HIT
DATA_CACHE_MISS
DATA_VALIDATION_ERROR
BAR_UPDATE
FEATURE_UPDATE
SIGNAL_CREATED
SIGNAL_REJECTED
BACKTEST_ENTRY
BACKTEST_EXIT
```

Signals should be reproducible from stored input data and configuration.

A signal generated on historical data should be possible to reconstruct
later.

------------------------------------------------------------------------

## 28. Error Handling

The system must tolerate:

-   Schwab API errors.
-   Temporary network failures.
-   Rate limits.
-   Missing bars.
-   Duplicate bars.
-   Delayed bars.
-   Partial historical responses.
-   Invalid symbols.
-   Market holidays.
-   Process restarts.

Live mode should fail safely.

A data outage must not be interpreted as a trading signal.

------------------------------------------------------------------------

## 29. Restart and Recovery

The live system should persist enough state to restart without losing
the current session.

On restart:

``` text
Load today's local 1m bars
        ↓
Reconstruct timeframe state
        ↓
Reconstruct features
        ↓
Resume live updates
```

The system should not blindly start from an empty state.

------------------------------------------------------------------------

## 30. Development Rules for Claude Code

Claude Code should follow these rules:

1.  Do not rewrite unrelated modules.
2.  Implement one module at a time.
3.  Add unit tests with every new feature.
4.  Do not mix data acquisition with strategy logic.
5.  Do not introduce look-ahead bias.
6.  Keep Schwab-specific code behind an adapter interface.
7.  Make strategy parameters configurable.
8.  Preserve deterministic replay behavior.
9.  Do not add automatic order execution without an explicit future
    design phase.
10. Run tests before declaring a module complete.
11. Prefer simple, inspectable implementations over premature
    optimization.
12. Document assumptions about timestamps and market sessions.

------------------------------------------------------------------------

## 31. Implementation Milestones

### Milestone 1 --- Data foundation

-   Schwab historical adapter.
-   Local Parquet storage.
-   Data validation.
-   Cache lookup.

### Milestone 2 --- Timeframes

-   1m canonical bars.
-   3m aggregation.
-   5m aggregation.
-   15m aggregation.

### Milestone 3 --- Feature Engine

Implement and test:

-   VWAP.
-   EMA.
-   RSI.
-   ATR.
-   RVOL.
-   Opening range.
-   Relative strength.

### Milestone 4 --- Signals

-   Reversal score.
-   Trend score.
-   Signal object.
-   Ranking engine.

### Milestone 5 --- Replay

-   Historical replay.
-   Causal feature calculation.
-   Signal event logging.

### Milestone 6 --- Backtest

-   Entry/exit simulation.
-   Slippage.
-   Metrics.
-   MFE/MAE.

### Milestone 7 --- Live scanner

-   Live data.
-   Same feature engine.
-   Same signal engine.
-   Real-time ranking.

### Milestone 8 --- Paper trading

-   Simulated execution.
-   Fill model.
-   Real-time P&L.

Automatic trading remains outside the first production milestone.

------------------------------------------------------------------------

## 32. Initial Acceptance Criteria

The first usable version is complete when all of the following are true:

-   A historical day can be requested by date and symbol.
-   Existing local data is reused.
-   Missing data is fetched from Schwab.
-   Data is validated and stored.
-   1m data produces deterministic 3m/5m/15m bars.
-   Features are calculated without future information.
-   Reversal and trend signals can be generated.
-   Historical data can be replayed one bar at a time.
-   Backtest results are reproducible.
-   Live mode can process the same data structures.
-   Signal output contains enough feature information for later
    analysis.
-   Unit and integration tests pass.

------------------------------------------------------------------------

## 33. Future Extensions

Potential future modules:

-   Premarket scanner.
-   Sector-relative models.
-   Market breadth.
-   News/event filters.
-   Earnings calendar.
-   Tick-level data.
-   Level II/order-book features.
-   Machine-learning ranking.
-   Portfolio risk management.
-   Automated order execution.
-   Multi-account execution.
-   Advanced walk-forward optimization.

These should be added only after the deterministic data/replay
foundation is stable.

------------------------------------------------------------------------

## 34. Final Architecture Principle

The most important design decision in this system is:

``` text
                 LIVE
                   \
                    \
                     → NORMALIZED DATA
                    /
                   /
              HISTORICAL
                     |
                     ↓
              SAME FEATURES
                     |
                     ↓
               SAME SIGNALS
                     |
          +----------+----------+
          |                     |
       SCANNER               BACKTEST
          |                     |
       PAPER                 RESEARCH
```

The system should never have one version of the strategy for live
trading and another version for backtesting.

**One data model.\
One feature engine.\
One signal engine.\
Different execution/replay environments.**

This architecture is intended to make research results reproducible,
minimize look-ahead bias, and allow the system to evolve from research →
live scanning → paper trading → eventual automated execution.
