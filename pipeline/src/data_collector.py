import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .config import PROCESSED_DIR, TOP_N_TOKENS
from .data_fetcher import CoinGeckoFetcher
from .models import TokenMarketData, TokenDetail


def _timestamp_to_date(ts_ms: float) -> date:
    return datetime.utcfromtimestamp(ts_ms / 1000).date()


def _extract_launch_price_and_date(chart_data: dict) -> tuple[Optional[float], Optional[date]]:
    """Extract the earliest price and date from market chart data."""
    prices = chart_data.get("prices", [])
    if not prices:
        return None, None
    first = prices[0]
    return first[1], _timestamp_to_date(first[0])


def _classify_category(categories: list[str]) -> str:
    """Map CoinGecko categories to simplified category labels."""
    cats_lower = [c.lower() for c in categories if c]

    # Check in priority order
    for cat in cats_lower:
        if "meme" in cat:
            return "Meme"
    for cat in cats_lower:
        if "layer 1" in cat or "smart contract" in cat:
            return "L1"
    for cat in cats_lower:
        if "layer 2" in cat or "rollup" in cat:
            return "L2"
    for cat in cats_lower:
        if "defi" in cat or "decentralized finance" in cat or "dex" in cat or "lending" in cat:
            return "DeFi"
    for cat in cats_lower:
        if "exchange" in cat:
            return "Exchange"
    for cat in cats_lower:
        if "stablecoin" in cat:
            return "Stablecoin"
    for cat in cats_lower:
        if "oracle" in cat or "infrastructure" in cat or "interop" in cat or "bridge" in cat:
            return "Infrastructure"
    for cat in cats_lower:
        if "gaming" in cat or "metaverse" in cat or "nft" in cat:
            return "Gaming/NFT"
    for cat in cats_lower:
        if "storage" in cat or "ai" in cat or "artificial" in cat:
            return "AI/Storage"

    return "Other"


def collect_all(fetcher: CoinGeckoFetcher, limit: Optional[int] = None) -> list[dict]:
    """
    Collect data for top tokens. Returns list of enriched token dicts.
    Pass limit=5 for testing with a small sample.
    """
    n = limit or TOP_N_TOKENS
    print(f"Fetching top {n} tokens by market cap...")
    raw_markets = fetcher.get_top_tokens(n)

    # Also fetch BTC chart for BTC-relative metrics
    print("Fetching BTC market chart...")
    btc_chart = fetcher.get_market_chart("bitcoin")
    btc_chart_path = PROCESSED_DIR / "btc_chart.json"
    btc_chart_path.write_text(json.dumps(btc_chart))

    tokens = []
    for i, raw in enumerate(raw_markets):
        market = TokenMarketData(**{k: raw.get(k) for k in TokenMarketData.model_fields})
        print(f"  [{i+1}/{n}] {market.name} ({market.id})...")

        # Fetch detail for genesis_date and categories
        try:
            detail_raw = fetcher.get_token_detail(market.id)
            genesis_str = detail_raw.get("genesis_date")
            genesis_date = date.fromisoformat(genesis_str) if genesis_str else None
            categories = detail_raw.get("categories") or []
        except Exception as e:
            print(f"    Warning: failed to fetch detail: {e}")
            genesis_date = None
            categories = []

        # Fetch market chart for launch price + fallback launch date
        try:
            chart = fetcher.get_market_chart(market.id)
            chart_price, chart_date = _extract_launch_price_and_date(chart)
        except Exception as e:
            print(f"    Warning: failed to fetch chart: {e}")
            chart_price, chart_date = None, None

        # Determine launch date and price
        if genesis_date:
            launch_date = genesis_date
            launch_source = "genesis_date"
            # Try to find price at genesis from chart
            launch_price = _price_at_date(chart.get("prices", []), genesis_date) if chart else chart_price
            if launch_price is None:
                launch_price = chart_price
        elif chart_date:
            launch_date = chart_date
            launch_source = "first_price"
            launch_price = chart_price
        else:
            launch_date = None
            launch_source = None
            launch_price = None

        token = {
            "id": market.id,
            "symbol": market.symbol,
            "name": market.name,
            "current_price": market.current_price,
            "market_cap": market.market_cap,
            "market_cap_rank": market.market_cap_rank,
            "ath": market.ath,
            "atl": market.atl,
            "image": market.image,
            "launch_date": launch_date.isoformat() if launch_date else None,
            "launch_price": launch_price,
            "launch_source": launch_source,
            "categories": categories,
            "category": _classify_category(categories),
        }
        tokens.append(token)

    # Save collected data
    out_path = PROCESSED_DIR / "collected_tokens.json"
    out_path.write_text(json.dumps(tokens, indent=2))
    print(f"Saved {len(tokens)} tokens to {out_path}")
    return tokens


def _price_at_date(prices: list, target: date) -> Optional[float]:
    """Find the price closest to a target date from chart data."""
    if not prices:
        return None
    best = None
    best_diff = float("inf")
    for ts_ms, price in prices:
        d = _timestamp_to_date(ts_ms)
        diff = abs((d - target).days)
        if diff < best_diff:
            best_diff = diff
            best = price
        if diff == 0:
            break
    return best
