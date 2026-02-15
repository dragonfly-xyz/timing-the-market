import json
import math
from datetime import date, datetime, timezone
from typing import Optional

from .config import PROCESSED_DIR
from .market_cycles import get_cycle_name, get_cycle_type


def _timestamp_to_date(ts_ms: float) -> date:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()


def _load_btc_chart() -> list:
    """Load BTC price history from processed data."""
    path = PROCESSED_DIR / "btc_chart.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return data.get("prices", [])


def _btc_price_at_date(btc_prices: list, target: date) -> Optional[float]:
    """Find BTC price closest to a target date. Returns None if closest is >30 days away."""
    if not btc_prices:
        return None
    best = None
    best_diff = float("inf")
    for ts_ms, price in btc_prices:
        d = _timestamp_to_date(ts_ms)
        diff = abs((d - target).days)
        if diff < best_diff:
            best_diff = diff
            best = price
        if diff == 0:
            break
    # Don't use a BTC price that's more than 30 days from the target date
    if best_diff > 30:
        return None
    return best


def compute_metrics(tokens: list[dict], today: Optional[date] = None) -> list[dict]:
    """Compute all metrics for each token. Mutates and returns the token dicts."""
    today = today or date.today()
    btc_prices = _load_btc_chart()

    # Current BTC price (last entry)
    btc_current = btc_prices[-1][1] if btc_prices else None

    for token in tokens:
        launch_str = token.get("launch_date")
        launch_date = date.fromisoformat(launch_str) if launch_str else None
        launch_price = token.get("launch_price")
        current_price = token.get("current_price")
        ath = token.get("ath")

        # Cycle classification
        token["cycle_name"] = get_cycle_name(launch_date)
        token["cycle_type"] = get_cycle_type(launch_date)

        # Age
        if launch_date:
            token["age_days"] = (today - launch_date).days
        else:
            token["age_days"] = None

        # ROI since launch — include tokens with current_price == 0 (dead tokens get -100%)
        if launch_price is not None and launch_price > 0 and current_price is not None:
            token["roi_since_launch"] = (current_price - launch_price) / launch_price
        else:
            token["roi_since_launch"] = None

        # Annualized ROI (CAGR) — require at least 365 days to avoid extrapolation artifacts
        roi = token["roi_since_launch"]
        age = token["age_days"]
        if roi is not None and age and age > 365:
            years = age / 365.25
            growth = 1 + roi
            if growth > 0:
                token["annualized_roi"] = math.pow(growth, 1 / years) - 1
            else:
                token["annualized_roi"] = -1.0
        else:
            token["annualized_roi"] = None

        # ROI vs BTC — geometric excess return
        if launch_date and btc_current is not None and launch_price is not None and launch_price > 0 and current_price is not None:
            btc_launch = _btc_price_at_date(btc_prices, launch_date)
            if btc_launch and btc_launch > 0:
                btc_roi = (btc_current - btc_launch) / btc_launch
                token_growth = 1 + (token["roi_since_launch"] or 0)
                btc_growth = 1 + btc_roi
                if btc_growth > 0:
                    token["roi_vs_btc"] = (token_growth / btc_growth) - 1
                else:
                    token["roi_vs_btc"] = None
            else:
                token["roi_vs_btc"] = None
        else:
            token["roi_vs_btc"] = None

        # Drawdown from ATH (current decline from peak, not historical max drawdown)
        if ath and ath > 0 and current_price is not None:
            token["drawdown_from_ath"] = max(0, (ath - current_price) / ath)
        else:
            token["drawdown_from_ath"] = None

    return tokens
