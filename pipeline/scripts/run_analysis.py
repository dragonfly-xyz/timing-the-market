#!/usr/bin/env python3
"""Run analysis on collected token data."""
import json
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from src.config import PROCESSED_DIR
from src.metrics import compute_metrics
from src.analyzer import compute_summary, compute_sensitivity, _filter_tokens
from src.exporter import export_for_website


def main():
    tokens_path = PROCESSED_DIR / "collected_tokens.json"
    if not tokens_path.exists():
        print(f"Error: {tokens_path} not found. Run collect_data.py first.")
        sys.exit(1)

    tokens = json.loads(tokens_path.read_text())
    print(f"Loaded {len(tokens)} tokens.")

    print("Computing metrics...")
    tokens = compute_metrics(tokens)

    print("Computing summary statistics...")
    summary = compute_summary(tokens)

    print("Computing sensitivity analysis...")
    sensitivity = compute_sensitivity(tokens)

    # Filter stablecoins/wrapped from the export so they don't appear in the table
    export_tokens, _, _ = _filter_tokens(tokens)
    print("Exporting for website...")
    export_for_website(export_tokens, summary, sensitivity)

    # Print key findings
    print("\n=== Key Findings ===")
    print(f"Tokens analyzed: {summary.total_tokens}")
    print(f"  Excluded stablecoins: {summary.tokens_excluded_stablecoin}")
    print(f"  Excluded wrapped: {summary.tokens_excluded_wrapped}")
    print(f"  Dead tokens imputed: {summary.tokens_imputed_dead}")
    print(f"Tokens by cycle type: {summary.tokens_by_cycle_type}")
    print(f"Median annualized ROI by cycle: {summary.median_annualized_roi_by_cycle_type}")
    print(f"Median ROI vs BTC by cycle: {summary.median_roi_vs_btc_by_cycle_type}")
    print(f"Fraction in top 100 by cycle: {summary.fraction_currently_top100_by_cycle_type}")

    if summary.bull_vs_bear_mannwhitney_pvalue is not None:
        print(f"\n--- Bull vs Bear (Annualized ROI) ---")
        print(f"  Bull n={summary.bull_n}, Bear n={summary.bear_n}")
        print(f"  Mann-Whitney p-value: {summary.bull_vs_bear_mannwhitney_pvalue:.4f}")
        print(f"  Effect size (rank-biserial): {summary.bull_vs_bear_effect_size:.4f}")
        print(f"  Median diff (bull - bear): {summary.bull_vs_bear_median_diff:.4f}")
        if summary.bull_vs_bear_ci_lower is not None:
            print(f"  95% CI: [{summary.bull_vs_bear_ci_lower:.4f}, {summary.bull_vs_bear_ci_upper:.4f}]")

    if summary.btc_rel_mannwhitney_pvalue is not None:
        print(f"\n--- Bull vs Bear (ROI vs BTC) ---")
        print(f"  Mann-Whitney p-value: {summary.btc_rel_mannwhitney_pvalue:.4f}")
        print(f"  Effect size (rank-biserial): {summary.btc_rel_effect_size:.4f}")
        print(f"  Median diff (bull - bear): {summary.btc_rel_median_diff:.4f}")
        if summary.btc_rel_ci_lower is not None:
            print(f"  95% CI: [{summary.btc_rel_ci_lower:.4f}, {summary.btc_rel_ci_upper:.4f}]")

    print(f"\n--- Sensitivity Analysis ---")
    for s in sensitivity:
        sig = "SIGNIFICANT" if s["significant"] else "not significant"
        p_str = f"p={s['pvalue']:.4f}" if s['pvalue'] is not None else "insufficient data"
        print(f"  Shift {s['shift_months']:+d}mo: {p_str} ({sig}) [bull={s['bull_n']}, bear={s['bear_n']}]")

    print("\nDone.")


if __name__ == "__main__":
    main()
