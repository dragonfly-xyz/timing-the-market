# Review Changelog

This document summarizes all changes made following the four independent code reviews (statistical analysis, Binance data integrity, data pipeline transcription, and research methodology).

---

## 1. Statistical Fixes

### Dead Token Imputation — Survivorship Bias Leak (Critical)

**Problem:** `_impute_dead_tokens()` set `roi_since_launch = -1.0` for dead tokens but left `annualized_roi` as `None`. Since the primary Mann-Whitney U test operates on `annualized_roi`, dead tokens were silently excluded from the main statistical comparison, creating a survivorship bias leak.

**Fix:** `pipeline/src/analyzer.py` — imputation now also sets `annualized_roi = -1.0` for dead tokens older than 365 days (the CAGR threshold). Tokens under 365 days still skip annualized ROI since CAGR is undefined for them.

```python
# Before: only roi_since_launch was imputed
t["roi_since_launch"] = -1.0

# After: annualized_roi also imputed for tokens old enough for CAGR
t["roi_since_launch"] = -1.0
if t.get("annualized_roi") is None and t.get("age_days") and t["age_days"] > 365:
    t["annualized_roi"] = -1.0
```

### NaN/Infinity Filtering Before Statistical Tests (Medium)

**Problem:** Extreme values (e.g. tokens with very small launch prices) could produce `float('inf')` ROI values. These pass Python's `is not None` check and enter `scipy.stats.mannwhitneyu`, potentially corrupting results or raising errors.

**Fix:** Added `_finite_values()` helper that filters out `NaN` and `Infinity` before all statistical test inputs (both annualized ROI and BTC-relative tests).

```python
def _finite_values(values: list[float]) -> list[float]:
    return [v for v in values if math.isfinite(v)]
```

### Sensitivity Analysis Effect Sizes (Medium)

**Problem:** The sensitivity analysis (`compute_sensitivity`) reported p-values but not effect sizes, making it impossible to assess practical significance at shifted boundaries.

**Fix:** Added rank-biserial effect size computation to each sensitivity shift result. Updated the `SensitivityResult` TypeScript interface to include `effect_size: number | null`.

### Dead Code Removal (Low)

Removed unused `total_before_filter` variable from `compute_summary()`.

---

## 2. Data Validation

### Pydantic Token Validation at Export (Medium)

**Problem:** The `TokenMetrics` Pydantic model existed in `models.py` but was never used to validate token data before export. Field name typos or type mismatches would only surface at website render time.

**Fix:** `pipeline/src/exporter.py` now runs every token through `TokenMetrics(**t)` before writing `tokens.json`. Validation failures log a warning but still include the token to avoid silent data loss.

---

## 3. Website Fixes

### MarketCycleChart Tooltip Flickering (P1)

**Problem:** The `<ComposedChart>` had an `onMouseMove` handler that checked pixel distance from the hovered dot on every mouse frame. Combined with a dual tooltip system (native Recharts + custom positioned div), this caused constant state re-evaluations and flicker.

**Fix:** Removed the `onMouseMove` handler from `<ComposedChart>` and the container `onMouseLeave`. Dot-level `onMouseEnter`/`onMouseLeave` handlers on each `<circle>` element are sufficient for clean tooltip behavior.

### Token Table Redesign (P2)

**File:** `website/src/components/tables/TokenTable.tsx`

| Change | Detail |
|--------|--------|
| Performance grade column | Percentile-based letter grade (A-F) computed from annualized ROI distribution. A = top 20%, F = bottom 20%. Color-coded badges. |
| Default sort | Changed from `market_cap_rank ascending` to `annualized_roi descending` — best performers shown first. |
| Removed columns | `#` (market cap rank), `Price` (absolute price is meaningless for comparison), `Market Cap` — grade replaces rank as the quick-scan metric. |
| Horizontal scroll | Added `min-w-[900px]` to inner `<table>` for predictable scroll inside `overflow-x-auto` container. |

### SurvivalRateChart Tooltip Label (Low)

Changed tooltip label from "Survival Rate" to "Fraction in Top 100" to match the actual metric being displayed (`fraction_currently_top100_by_cycle_type`).

---

## 4. Test Updates

| File | Change |
|------|--------|
| `pipeline/tests/test_analyzer.py` | Updated `test_imputes_delisted_no_price` to assert `annualized_roi == -1.0`. Added `test_imputes_roi_but_not_annualized_for_young_tokens` (age < 365d). Updated sensitivity test to verify `effect_size` in results. |
| `website/e2e/explorer.spec.ts` | Updated header check from `"Price"` to `"Grade"` after column removal. |

---

## 5. Verification

- Pipeline tests: **37/37 passed** (`PYTHONPATH=. pytest pipeline/tests/ -v`)
- Website build: **Compiled successfully** (`npm run build`)
- Playwright E2E tests: **63/63 passed** (`npx playwright test`)

---

## Files Modified

| File | Lines Changed | Summary |
|------|--------------|---------|
| `pipeline/src/analyzer.py` | ~30 | Dead token imputation fix, NaN filtering, sensitivity effect sizes, dead code removal |
| `pipeline/src/exporter.py` | ~20 | Added Pydantic `TokenMetrics` validation before export |
| `pipeline/tests/test_analyzer.py` | ~15 | Updated/added tests for imputation and sensitivity |
| `website/src/components/charts/MarketCycleChart.tsx` | ~5 | Removed onMouseMove tooltip handler |
| `website/src/components/tables/TokenTable.tsx` | ~100 | Grade column, default sort, column reduction, scroll fix |
| `website/src/components/charts/SurvivalRateChart.tsx` | ~1 | Tooltip label correction |
| `website/src/types.ts` | ~1 | Added `effect_size` to `SensitivityResult` |
| `website/e2e/explorer.spec.ts` | ~1 | Header assertion update |
