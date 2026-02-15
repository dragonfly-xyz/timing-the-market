# Code Review Findings

Findings from 4 automated review subagents run on 2026-02-14, updated 2026-02-15, covering: statistical analysis, data integrity, pipeline transcription, and research methodology.

## Fixes Applied

The following issues were identified and fixed:

| Issue | Severity | Fix |
|-------|----------|-----|
| `NameError` in `binance_collector.py:182` — `symbol` undefined, should be `sym` | CRITICAL | Changed `symbol=symbol` to `symbol=sym` |
| `LaunchDistribution.tsx` CYCLE_ORDER missing "2025-2026 Bear" | WARNING | Added to CYCLE_ORDER array |
| Drawdown display shows `-0.0%` when token is at ATH | WARNING | Added `v === 0` check to show `0.0%` |
| `STABLECOIN_SYMBOLS` duplicated in `analyzer.py` and `binance_collector.py` | NOTE | Consolidated into `config.py`, both modules import from there |

## Acknowledged Limitations

These are methodological limitations that are documented but do not require code changes:

### Token Age Confound
Annualized ROI (CAGR) is confounded with token age. Older tokens that survive represent a selection effect. The study compares tokens of different ages because bull and bear markets occurred at different times. This is inherent to the research question and disclosed on the methodology page.

### Multiple Testing
Two primary tests are run (annualized ROI and BTC-relative). No Bonferroni correction is applied. Since both tests return non-significant results (p=0.48 and p=0.78), the false positive concern is moot for the current data. If the result ever becomes significant, correction should be applied.

### Binance-Only Sampling Frame
Only tokens listed on Binance are included. Binance's listing criteria may vary by market cycle (more selective during bears), which could confound the comparison. This is disclosed on the methodology page.

### Binance CMS Scraper Coverage
The scraper matches "Binance Will List" title format, which misses some older listing announcements that used different formats ("Binance Lists X", "Launchpool", etc.). The current dataset of 225 tokens covers the period from 2018 onward well but underrepresents pre-2018 tokens. Tokens with earlier CoinGecko genesis dates still get correctly classified by cycle via the genesis_date preference logic.

### Market Cycle Boundary Definitions
Cycle boundaries are hard-coded based on historical BTC price movements. The 2025-2026 Bear classification is provisional. Two robustness checks confirm the result is not an artifact of boundary definitions:
1. **Sensitivity analysis**: Shifting boundaries by +/- 1-2 months — all produce non-significant results.
2. **MA robustness check**: Replacing hand-labeled cycles entirely with BTC N-day SMA regime classification (50/100/200/300-day windows) — all p-values non-significant. The lowest (p=0.079 at 50-day) is well above the Bonferroni-corrected threshold of 0.0125.

### Dead Token Imputation
Setting ROI = -1.0 for dead tokens creates a mass point at -100%. This is conservative and symmetric (applies to both groups). The imputation rate by group: Bull 16.7% delisted, Bear 12.3% delisted. The imputation prevents survivorship bias.

### Neutral Token Exclusion
Tokens launched during "Recovery" periods (20 tokens) are excluded from the primary Bull vs Bear test. This is a design choice to test the clearest bull/bear contrast.

### BTC-Relative Metric Endogeneity
The BTC-relative return is partially endogenous to cycle classification since BTC's performance differs by cycle. This metric is secondary and not used for the main verdict.

### Anchoring / Launch-Day Valuation Objection
If bull tokens launch at higher FDVs and ROI is the same, bull tokens would maintain higher absolute dollar valuations. Tested empirically using launch-day circulating market cap (from CoinGecko chart history), FDV proxy (launch price x total supply), and current market cap. Result: bear tokens actually launched at somewhat higher median market caps. No evidence of persistent launch-day valuation premium. Analysis displayed on the analysis page.

### Sample Size Imbalance
105 Bull vs 39 Bear tokens. Mann-Whitney U handles unequal sizes, but the smaller bear group limits precision. Bootstrap CI quantifies this uncertainty.

## Issues Not Requiring Action

### Statistical Methodology (All Correct)
- Mann-Whitney U test implementation is correct and appropriate
- Rank-biserial effect size formula is correct
- Bootstrap 95% CI (percentile method, 10K resamples, seed=42) is standard
- Geometric BTC-relative return `(1+token)/(1+btc)-1` is correct
- CAGR formula with 365-day minimum threshold is correct
- Dead token imputation is idempotent (safe despite shared mutable state)

### Shared Mutable State Between Pipeline Stages
`compute_summary` and `compute_sensitivity` both mutate token dicts via `_impute_dead_tokens`. This works correctly because imputation is idempotent, but the calling order matters. Documented as technical debt.

### CoinGecko Cache Expiration
The file-based cache never expires. This is fine for one-time analysis but means re-runs without clearing cache produce stale results. By design for reproducibility.

### Stale Data Warnings
Several review findings about stale data are addressed by the genesis date fix script and re-running analysis. Wrong CoinGecko ID mappings (BTCB, BOT, VAI) were from the initial collection and have been corrected by the `fix_genesis_dates.py` script.
