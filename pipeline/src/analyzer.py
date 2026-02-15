import math

import numpy as np
from scipy import stats
from datetime import date
from typing import Optional

from .config import STABLECOIN_SYMBOLS
from .models import SummaryStats
from .market_cycles import MARKET_CYCLES, classify_launch_date

# Minimum sample size per group for statistical tests
MIN_SAMPLE_SIZE = 20
# Number of bootstrap resamples for confidence intervals
N_BOOTSTRAP = 10_000


def _finite_values(values: list[float]) -> list[float]:
    """Filter out NaN and Infinity values before statistical tests."""
    return [v for v in values if math.isfinite(v)]


def _median(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return float(np.median(values))


def _filter_tokens(tokens: list[dict]) -> tuple[list[dict], int, int]:
    """Remove stablecoins and wrapped tokens from analysis.

    Returns (filtered_tokens, n_stablecoin_excluded, n_wrapped_excluded).
    """
    n_stable = 0
    n_wrapped = 0
    filtered = []
    for t in tokens:
        cat = t.get("category", "")
        sym = t.get("symbol", "").lower()
        if cat == "Stablecoin" or sym in STABLECOIN_SYMBOLS:
            n_stable += 1
        elif cat == "Wrapped":
            n_wrapped += 1
        else:
            filtered.append(t)
    return filtered, n_stable, n_wrapped


def _impute_dead_tokens(tokens: list[dict]) -> int:
    """Impute -100% ROI for delisted tokens with no price data.

    These are tokens that were delisted from Binance and have no current price
    data — they're effectively dead. Without imputation they'd be silently
    excluded from statistical tests, biasing results upward.

    Sets both roi_since_launch and annualized_roi to -1.0 (total loss) so that
    dead tokens are included in the primary Mann-Whitney test on annualized ROI,
    not just in the roi_since_launch medians.

    Returns count of imputed tokens.
    """
    count = 0
    for t in tokens:
        if (t.get("binance_delisted")
                and t.get("roi_since_launch") is None
                and t.get("current_price") is None):
            t["roi_since_launch"] = -1.0  # total loss
            # Also set annualized_roi so dead tokens enter the primary statistical test
            if t.get("annualized_roi") is None and t.get("age_days") and t["age_days"] > 365:
                t["annualized_roi"] = -1.0
            count += 1
    return count


def _group_by_cycle_type(tokens: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for t in tokens:
        ct = t.get("cycle_type")
        if ct and ct != "Unknown":
            groups.setdefault(ct, []).append(t)
    return groups


def _bootstrap_median_diff_ci(
    a: list[float], b: list[float], n_resamples: int = N_BOOTSTRAP, ci: float = 0.95
) -> tuple[Optional[float], Optional[float]]:
    """Bootstrap 95% CI for difference in medians (a_median - b_median)."""
    if len(a) < 2 or len(b) < 2:
        return None, None
    rng = np.random.default_rng(42)
    arr_a = np.array(a)
    arr_b = np.array(b)
    diffs = np.empty(n_resamples)
    for i in range(n_resamples):
        sample_a = rng.choice(arr_a, size=len(arr_a), replace=True)
        sample_b = rng.choice(arr_b, size=len(arr_b), replace=True)
        diffs[i] = float(np.median(sample_a) - np.median(sample_b))
    alpha = (1 - ci) / 2
    lower = float(np.percentile(diffs, alpha * 100))
    upper = float(np.percentile(diffs, (1 - alpha) * 100))
    return lower, upper


def _rank_biserial(u_stat: float, n1: int, n2: int) -> float:
    """Compute rank-biserial correlation as effect size for Mann-Whitney U."""
    return 2 * u_stat / (n1 * n2) - 1


def _run_statistical_tests(
    bull_values: list[float], bear_values: list[float]
) -> dict:
    """Run Mann-Whitney U test with effect size and bootstrap CI."""
    result = {
        "mannwhitney_pvalue": None,
        "effect_size": None,
        "median_diff": None,
        "ci_lower": None,
        "ci_upper": None,
    }

    if len(bull_values) < MIN_SAMPLE_SIZE or len(bear_values) < MIN_SAMPLE_SIZE:
        return result

    # Mann-Whitney U (non-parametric, doesn't assume normality)
    u_stat, p_value = stats.mannwhitneyu(
        bull_values, bear_values, alternative="two-sided"
    )
    result["mannwhitney_pvalue"] = float(p_value)

    # Effect size: rank-biserial correlation
    result["effect_size"] = _rank_biserial(u_stat, len(bull_values), len(bear_values))

    # Difference in medians
    result["median_diff"] = float(np.median(bull_values) - np.median(bear_values))

    # Bootstrap 95% CI for difference in medians
    ci_lower, ci_upper = _bootstrap_median_diff_ci(bull_values, bear_values)
    result["ci_lower"] = ci_lower
    result["ci_upper"] = ci_upper

    return result


def compute_summary(tokens: list[dict]) -> SummaryStats:
    """Compute aggregate summary statistics.

    Filters out stablecoins/wrapped tokens, imputes dead tokens,
    then computes group-level stats and statistical tests.
    """
    # Filter contaminants
    tokens, n_stable, n_wrapped = _filter_tokens(tokens)

    # Impute -100% ROI for dead (delisted, no price) tokens
    n_imputed = _impute_dead_tokens(tokens)

    tokens_with_date = [t for t in tokens if t.get("launch_date")]
    groups = _group_by_cycle_type(tokens)

    # Counts per cycle type
    tokens_by_cycle = {k: len(v) for k, v in groups.items()}

    # Median metrics by cycle type
    median_roi = {}
    median_ann_roi = {}
    median_roi_vs_btc = {}
    median_drawdown = {}
    fraction_top100 = {}

    for cycle_type, group in groups.items():
        rois = [t["roi_since_launch"] for t in group if t.get("roi_since_launch") is not None]
        ann_rois = [t["annualized_roi"] for t in group if t.get("annualized_roi") is not None]
        btc_rois = [t["roi_vs_btc"] for t in group if t.get("roi_vs_btc") is not None]
        drawdowns = [t["drawdown_from_ath"] for t in group if t.get("drawdown_from_ath") is not None]

        median_roi[cycle_type] = _median(rois)
        median_ann_roi[cycle_type] = _median(ann_rois)
        median_roi_vs_btc[cycle_type] = _median(btc_rois)
        median_drawdown[cycle_type] = _median(drawdowns)

        # Fraction currently in top 100 (not "survival rate")
        in_top100 = sum(1 for t in group if (t.get("market_cap_rank") or 999) <= 100)
        fraction_top100[cycle_type] = in_top100 / len(group) if group else None

    # Delist rate by cycle type (fraction delisted from Binance)
    delist_rate = {}
    for cycle_type, group in groups.items():
        delisted = sum(1 for t in group if t.get("binance_delisted"))
        delist_rate[cycle_type] = delisted / len(group) if group else None

    # Statistical tests: Bull vs Bear (filter NaN/Infinity before tests)
    bull_ann_rois = _finite_values([t["annualized_roi"] for t in groups.get("Bull", []) if t.get("annualized_roi") is not None])
    bear_ann_rois = _finite_values([t["annualized_roi"] for t in groups.get("Bear", []) if t.get("annualized_roi") is not None])
    ann_roi_tests = _run_statistical_tests(bull_ann_rois, bear_ann_rois)

    # BTC-relative tests (filter NaN/Infinity before tests)
    bull_btc = _finite_values([t["roi_vs_btc"] for t in groups.get("Bull", []) if t.get("roi_vs_btc") is not None])
    bear_btc = _finite_values([t["roi_vs_btc"] for t in groups.get("Bear", []) if t.get("roi_vs_btc") is not None])
    btc_tests = _run_statistical_tests(bull_btc, bear_btc)

    # Best/worst performers by annualized ROI
    ranked = sorted(
        [t for t in tokens if t.get("annualized_roi") is not None],
        key=lambda t: t["annualized_roi"],
        reverse=True,
    )
    best = [_summary_token(t) for t in ranked[:10]]
    worst = [_summary_token(t) for t in ranked[-10:]]

    return SummaryStats(
        total_tokens=len(tokens),
        tokens_with_launch_date=len(tokens_with_date),
        tokens_by_cycle_type=tokens_by_cycle,
        median_roi_by_cycle_type=median_roi,
        median_annualized_roi_by_cycle_type=median_ann_roi,
        median_roi_vs_btc_by_cycle_type=median_roi_vs_btc,
        fraction_currently_top100_by_cycle_type=fraction_top100,
        median_drawdown_by_cycle_type=median_drawdown,
        delist_rate_by_cycle_type=delist_rate,
        best_performers=best,
        worst_performers=worst,
        # Annualized ROI tests
        bull_vs_bear_mannwhitney_pvalue=ann_roi_tests["mannwhitney_pvalue"],
        bull_vs_bear_effect_size=ann_roi_tests["effect_size"],
        bull_vs_bear_median_diff=ann_roi_tests["median_diff"],
        bull_vs_bear_ci_lower=ann_roi_tests["ci_lower"],
        bull_vs_bear_ci_upper=ann_roi_tests["ci_upper"],
        bull_n=len(bull_ann_rois) if bull_ann_rois else None,
        bear_n=len(bear_ann_rois) if bear_ann_rois else None,
        # BTC-relative tests
        btc_rel_mannwhitney_pvalue=btc_tests["mannwhitney_pvalue"],
        btc_rel_effect_size=btc_tests["effect_size"],
        btc_rel_median_diff=btc_tests["median_diff"],
        btc_rel_ci_lower=btc_tests["ci_lower"],
        btc_rel_ci_upper=btc_tests["ci_upper"],
        # Transparency counts
        tokens_excluded_stablecoin=n_stable,
        tokens_excluded_wrapped=n_wrapped,
        tokens_imputed_dead=n_imputed,
    )


def compute_sensitivity(tokens: list[dict]) -> list[dict]:
    """Test sensitivity of Mann-Whitney result to cycle boundary shifts.

    Shifts each cycle boundary by -2, -1, +1, +2 months and re-runs the test.
    Returns list of {shift_months, pvalue, conclusion} dicts.
    """
    from datetime import timedelta

    # Filter tokens same as compute_summary
    tokens, _, _ = _filter_tokens(tokens)
    _impute_dead_tokens(tokens)

    results = []
    for shift_months in [-2, -1, 0, 1, 2]:
        shift_days = shift_months * 30  # approximate

        # Re-classify tokens with shifted boundaries
        bull_rois = []
        bear_rois = []
        for t in tokens:
            launch_str = t.get("launch_date")
            ann_roi = t.get("annualized_roi")
            if not launch_str or ann_roi is None or not math.isfinite(ann_roi):
                continue

            launch_date = date.fromisoformat(launch_str)
            # Shift the launch date (equivalent to shifting boundaries the other way)
            shifted = launch_date - timedelta(days=shift_days)
            cycle = classify_launch_date(shifted)
            ct = cycle["type"]

            if ct == "Bull":
                bull_rois.append(ann_roi)
            elif ct == "Bear":
                bear_rois.append(ann_roi)

        p_value = None
        effect_size = None
        if len(bull_rois) >= MIN_SAMPLE_SIZE and len(bear_rois) >= MIN_SAMPLE_SIZE:
            u_stat, p_value = stats.mannwhitneyu(bull_rois, bear_rois, alternative="two-sided")
            p_value = float(p_value)
            effect_size = _rank_biserial(u_stat, len(bull_rois), len(bear_rois))

        results.append({
            "shift_months": shift_months,
            "pvalue": p_value,
            "effect_size": effect_size,
            "bull_n": len(bull_rois),
            "bear_n": len(bear_rois),
            "significant": p_value is not None and p_value < 0.05,
        })

    return results


def compute_ma_robustness(tokens: list[dict], btc_prices: list) -> list[dict]:
    """Test robustness using BTC moving average regime classification.

    Instead of hand-labeled cycles, classifies bull/bear by whether BTC was
    above/below its N-day SMA at each token's launch date.
    Returns results for multiple MA windows.
    """
    from datetime import datetime, timezone, timedelta

    tokens, _, _ = _filter_tokens(tokens)
    _impute_dead_tokens(tokens)

    # Build daily BTC price dict from [timestamp_ms, price] pairs
    btc_daily = {}
    for ts_ms, price in btc_prices:
        d = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
        btc_daily[d] = price
    sorted_dates = sorted(btc_daily.keys())
    prices_list = [btc_daily[d] for d in sorted_dates]

    results = []
    for window in [50, 100, 200, 300]:
        # Compute SMA
        sma = {}
        for i, d in enumerate(sorted_dates):
            if i >= window - 1:
                w = prices_list[i - window + 1:i + 1]
                sma[d] = sum(w) / len(w)

        bull_rois = []
        bear_rois = []
        for t in tokens:
            launch_str = t.get("launch_date")
            ann_roi = t.get("annualized_roi")
            if not launch_str or ann_roi is None or not math.isfinite(ann_roi):
                continue

            ld = date.fromisoformat(launch_str)
            # Find closest date with SMA data
            if ld not in sma:
                found = False
                for offset in range(1, 8):
                    for candidate in [ld + timedelta(days=offset), ld - timedelta(days=offset)]:
                        if candidate in sma:
                            ld = candidate
                            found = True
                            break
                    if found:
                        break
                if not found:
                    continue

            btc_price = btc_daily.get(ld)
            ma = sma.get(ld)
            if btc_price is None or ma is None:
                continue

            if btc_price > ma:
                bull_rois.append(ann_roi)
            else:
                bear_rois.append(ann_roi)

        p_value = None
        effect_size = None
        if len(bull_rois) >= MIN_SAMPLE_SIZE and len(bear_rois) >= MIN_SAMPLE_SIZE:
            u_stat, p_value = stats.mannwhitneyu(
                bull_rois, bear_rois, alternative="two-sided"
            )
            p_value = float(p_value)
            effect_size = _rank_biserial(u_stat, len(bull_rois), len(bear_rois))

        results.append({
            "window": window,
            "pvalue": p_value,
            "effect_size": effect_size,
            "bull_n": len(bull_rois),
            "bear_n": len(bear_rois),
            "significant": p_value is not None and p_value < 0.05,
        })

    return results


def _summary_token(t: dict) -> dict:
    return {
        "id": t["id"],
        "symbol": t["symbol"],
        "name": t["name"],
        "cycle_type": t.get("cycle_type"),
        "cycle_name": t.get("cycle_name"),
        "annualized_roi": t.get("annualized_roi"),
        "roi_since_launch": t.get("roi_since_launch"),
        "roi_vs_btc": t.get("roi_vs_btc"),
        "market_cap_rank": t.get("market_cap_rank"),
        "binance_delisted": t.get("binance_delisted", False),
    }
