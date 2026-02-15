import json
import math
from .config import WEBSITE_DATA_DIR, PROCESSED_DIR
from .market_cycles import get_all_cycles
from .models import SummaryStats, TokenMetrics


def _sanitize(obj):
    """Replace NaN and Infinity with None to produce valid JSON."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _validate_tokens(tokens: list[dict]) -> list[dict]:
    """Validate token dicts against the TokenMetrics Pydantic model.

    Catches field name typos, type mismatches, and missing required fields
    at pipeline time rather than at website render time.
    """
    validated = []
    for t in tokens:
        try:
            model = TokenMetrics(**t)
            validated.append(model.model_dump())
        except Exception as e:
            print(f"  Warning: token '{t.get('symbol', '?')}' failed validation: {e}")
            validated.append(t)  # include anyway to avoid silent data loss
    return validated


def export_for_website(tokens: list[dict], summary: SummaryStats, sensitivity: list[dict] | None = None):
    """Export all computed data as JSON files for the Next.js website."""

    # 1. tokens.json — validate through Pydantic model, then sanitize
    print("Validating tokens against TokenMetrics schema...")
    tokens = _validate_tokens(tokens)
    tokens_path = WEBSITE_DATA_DIR / "tokens.json"
    tokens_path.write_text(json.dumps(_sanitize(tokens), indent=2))
    print(f"Exported {len(tokens)} tokens to {tokens_path}")

    # 2. summary_stats.json (sanitized)
    summary_path = WEBSITE_DATA_DIR / "summary_stats.json"
    summary_path.write_text(json.dumps(_sanitize(summary.model_dump()), indent=2))
    print(f"Exported summary stats to {summary_path}")

    # 3. market_cycles.json
    cycles_path = WEBSITE_DATA_DIR / "market_cycles.json"
    cycles_path.write_text(json.dumps(get_all_cycles(), indent=2))
    print(f"Exported market cycles to {cycles_path}")

    # 4. btc_history.json — simplified BTC price history for chart backdrop
    btc_chart_path = PROCESSED_DIR / "btc_chart.json"
    if btc_chart_path.exists():
        btc_data = json.loads(btc_chart_path.read_text())
        # Downsample to weekly for smaller file size
        prices = btc_data.get("prices", [])
        weekly = prices[::7]  # every 7th data point
        btc_out = WEBSITE_DATA_DIR / "btc_history.json"
        btc_out.write_text(json.dumps(weekly))
        size_kb = btc_out.stat().st_size / 1024
        print(f"Exported BTC history ({len(weekly)} points, {size_kb:.0f}KB) to {btc_out}")

    # 5. sensitivity.json — cycle boundary sensitivity analysis
    if sensitivity is not None:
        sensitivity_path = WEBSITE_DATA_DIR / "sensitivity.json"
        sensitivity_path.write_text(json.dumps(_sanitize(sensitivity), indent=2))
        print(f"Exported sensitivity analysis to {sensitivity_path}")
