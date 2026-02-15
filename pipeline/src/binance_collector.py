"""
Collect data using Binance listings as the primary dataset.

Instead of taking today's top 200 (survivorship bias), we use every token
ever listed on Binance spot market. This includes tokens that were later
delisted — the failures that a top-200 approach would miss.

For each listed token, we fetch current/last-known price data from CoinGecko
to compute performance metrics.
"""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from .config import PROCESSED_DIR, STABLECOIN_SYMBOLS
from .binance_fetcher import BinanceFetcher
from .data_fetcher import CoinGeckoFetcher


# Manual CoinGecko ID overrides for known symbol collisions
CG_OVERRIDES = {
    "BTCB": "bitcoin-bep2",
    "LUNA": "terra-luna-2",
    "WBTC": "wrapped-bitcoin",
    "WETH": "weth",
    "STETH": "staked-ether",
    "WBETH": "wrapped-beacon-eth",
    "RETH": "rocket-pool-eth",
    "CBETH": "coinbase-wrapped-staked-eth",
}


def _normalize_symbol(symbol: str) -> str:
    """Normalize a symbol for matching (strip 1000x prefix, lowercase)."""
    s = symbol.upper().strip()
    # Remove 1000 prefix (e.g. 1000CHEEMS -> CHEEMS)
    s = re.sub(r"^1000", "", s)
    return s


def _build_delist_map(delistings: list[dict]) -> dict[str, str]:
    """Build symbol -> earliest delist date map."""
    dmap: dict[str, str] = {}
    for d in delistings:
        sym = d.get("token_symbol")
        if not sym:
            continue
        ddate = d.get("delist_date", "")
        norm = _normalize_symbol(sym)
        if norm not in dmap or ddate < dmap[norm]:
            dmap[norm] = ddate
    return dmap


def collect_binance_tokens(
    binance: BinanceFetcher,
    coingecko: CoinGeckoFetcher,
    limit: Optional[int] = None,
) -> list[dict]:
    """
    Collect all Binance-listed tokens with enriched data from CoinGecko.

    Returns list of token dicts with listing date, delist status, and price data.
    """
    print("=== Phase 1: Fetching Binance listing/delisting history ===")
    listings = binance.get_listings()
    delistings = binance.get_delistings()
    delist_map = _build_delist_map(delistings)

    print(f"\n  {len(listings)} unique token listings found")
    print(f"  {len(delist_map)} unique delisted tokens")

    # Filter to tokens with symbols only
    listings = [l for l in listings if l.get("token_symbol")]
    if limit:
        listings = listings[:limit]

    print(f"  Processing {len(listings)} tokens with symbols\n")

    # Also fetch BTC chart for BTC-relative metrics
    print("=== Phase 2: Fetching BTC price history ===")
    btc_chart = coingecko.get_market_chart("bitcoin")
    btc_chart_path = PROCESSED_DIR / "btc_chart.json"
    btc_chart_path.write_text(json.dumps(btc_chart))

    # Try to match each Binance-listed token to a CoinGecko ID
    # First, build a symbol -> CoinGecko mapping from top tokens
    print("\n=== Phase 3: Building CoinGecko symbol mapping ===")
    cg_map = _build_coingecko_map(coingecko)

    # Apply manual overrides (these take priority over symbol-based lookup)
    for sym, cg_id in CG_OVERRIDES.items():
        cg_map[sym] = cg_id

    print(f"\n=== Phase 4: Enriching {len(listings)} tokens with CoinGecko data ===")
    tokens = []
    for i, listing in enumerate(listings):
        sym = listing["token_symbol"]
        norm_sym = _normalize_symbol(sym)
        name = listing["token_name"]
        listing_date = listing["listing_date"]
        is_delisted = norm_sym in delist_map
        delist_date = delist_map.get(norm_sym)

        print(f"  [{i+1}/{len(listings)}] {name} ({sym})"
              f"{' [DELISTED]' if is_delisted else ''}...")

        # Try to find CoinGecko ID
        cg_id = cg_map.get(norm_sym) or cg_map.get(sym.upper())

        current_price = None
        market_cap = None
        market_cap_rank = None
        ath = None
        atl = None
        image = None
        launch_price = None
        categories = []
        category = None
        genesis_date_str = None
        launch_date = listing_date
        launch_source = "binance_listing"

        if cg_id:
            # Fetch detail (includes genesis_date and categories)
            try:
                detail = coingecko.get_token_detail(cg_id)
                categories = detail.get("categories") or []

                # Use genesis_date if available and earlier than Binance listing
                raw_genesis = detail.get("genesis_date")
                if raw_genesis:
                    genesis_date_str = raw_genesis
                    try:
                        genesis = date.fromisoformat(raw_genesis)
                        listing_d = date.fromisoformat(listing_date)
                        if genesis < listing_d:
                            launch_date = raw_genesis
                            launch_source = "coingecko_genesis"
                    except (ValueError, TypeError):
                        pass
            except Exception as e:
                print(f"    Warning: detail fetch failed: {e}")

            # Fetch market chart for launch price
            try:
                chart = coingecko.get_market_chart(cg_id)
                prices = chart.get("prices", [])
                if prices:
                    launch_price = _price_at_date(prices, date.fromisoformat(launch_date))
            except Exception as e:
                print(f"    Warning: chart fetch failed: {e}")

            # Get current market data from the markets list if available
            market_info = _cg_markets.get(cg_id)
            if market_info:
                current_price = market_info.get("current_price")
                market_cap = market_info.get("market_cap")
                market_cap_rank = market_info.get("market_cap_rank")
                ath = market_info.get("ath")
                atl = market_info.get("atl")
                image = market_info.get("image")
        else:
            print(f"    No CoinGecko match found")

        token = {
            "id": cg_id or f"binance-{norm_sym.lower()}",
            "symbol": sym.lower(),
            "name": name,
            "current_price": current_price,
            "market_cap": market_cap,
            "market_cap_rank": market_cap_rank,
            "ath": ath,
            "atl": atl,
            "image": image,
            "launch_date": launch_date,
            "launch_price": launch_price,
            "launch_source": launch_source,
            "categories": categories,
            "category": _classify_category(categories, symbol=sym),
            "binance_listed": True,
            "binance_delisted": is_delisted,
            "binance_delist_date": delist_date,
        }
        tokens.append(token)

    # Save
    out_path = PROCESSED_DIR / "collected_tokens.json"
    out_path.write_text(json.dumps(tokens, indent=2))
    print(f"\nSaved {len(tokens)} tokens to {out_path}")

    # Stats
    delisted_count = sum(1 for t in tokens if t["binance_delisted"])
    with_price = sum(1 for t in tokens if t["current_price"] is not None)
    genesis_count = sum(1 for t in tokens if t["launch_source"] == "coingecko_genesis")
    print(f"  Delisted: {delisted_count}")
    print(f"  With CoinGecko price data: {with_price}")
    print(f"  Using genesis_date as launch: {genesis_count}")

    return tokens


# Module-level cache for CoinGecko market data
_cg_markets: dict[str, dict] = {}


def _build_coingecko_map(cg: CoinGeckoFetcher) -> dict[str, str]:
    """Build symbol -> CoinGecko ID mapping using top tokens."""
    global _cg_markets
    symbol_map: dict[str, str] = {}

    # Fetch a large set of tokens from CoinGecko
    for page in range(1, 11):  # Top 2500 tokens
        try:
            data = cg._request(
                "/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": page,
                    "sparkline": "false",
                },
                cache_key=f"markets_page_{page}",
            )
            for coin in data:
                sym = coin.get("symbol", "").upper()
                cg_id = coin.get("id", "")
                if sym and cg_id:
                    # Prefer the first (higher market cap) mapping
                    if sym not in symbol_map:
                        symbol_map[sym] = cg_id
                    _cg_markets[cg_id] = coin
        except Exception as e:
            print(f"  Warning: failed to fetch market page {page}: {e}")
            break

    print(f"  Built mapping for {len(symbol_map)} symbols from CoinGecko")
    return symbol_map


def _price_at_date(prices: list, target: date) -> Optional[float]:
    """Find the price closest to a target date from chart data."""
    if not prices:
        return None
    best = None
    best_diff = float("inf")
    for ts_ms, price in prices:
        d = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
        diff = abs((d - target).days)
        if diff < best_diff:
            best_diff = diff
            best = price
        if diff == 0:
            break
    # Only return if within 7 days of target
    if best_diff <= 7:
        return best
    return None


def _classify_category(categories: list[str], symbol: str = "") -> str:
    """Map CoinGecko categories to simplified labels.

    Priority order matters: stablecoins and wrapped tokens are checked first
    to prevent misclassification (e.g. sUSD being classified as DeFi).
    """
    # 0. Symbol-based stablecoin override for tokens CoinGecko miscategorizes
    if symbol.lower() in STABLECOIN_SYMBOLS:
        return "Stablecoin"

    cats_lower = [c.lower() for c in categories if c]

    # 1. Stablecoin — check first, but exclude pure "stablecoin issuer" governance tokens
    for cat in cats_lower:
        if "stablecoin" in cat and "issuer" not in cat:
            return "Stablecoin"

    # 2. Wrapped/Staked/Bridged tokens — these track other assets, not independent
    for cat in cats_lower:
        if "wrapped" in cat or "bridged" in cat or "liquid staking" in cat:
            return "Wrapped"

    # 3. Meme
    for cat in cats_lower:
        if "meme" in cat:
            return "Meme"

    # 4. L1
    for cat in cats_lower:
        if "layer 1" in cat or "smart contract" in cat:
            return "L1"

    # 5. L2
    for cat in cats_lower:
        if "layer 2" in cat or "rollup" in cat:
            return "L2"

    # 6. DeFi
    for cat in cats_lower:
        if "defi" in cat or "decentralized finance" in cat or "dex" in cat or "lending" in cat:
            return "DeFi"

    # 7. Exchange
    for cat in cats_lower:
        if "exchange" in cat:
            return "Exchange"

    # 8. Infrastructure
    for cat in cats_lower:
        if "oracle" in cat or "infrastructure" in cat or "interop" in cat or "bridge" in cat:
            return "Infrastructure"

    # 9. Gaming/NFT
    for cat in cats_lower:
        if "gaming" in cat or "metaverse" in cat or "nft" in cat:
            return "Gaming/NFT"

    # 10. AI/Storage
    for cat in cats_lower:
        if "storage" in cat or "ai" in cat or "artificial" in cat:
            return "AI/Storage"

    return "Other"
