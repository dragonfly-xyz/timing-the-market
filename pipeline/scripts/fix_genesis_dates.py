"""
Fix tokens with binance- prefix IDs by looking them up on CoinGecko.

These tokens didn't match during initial collection. This script:
1. Maps their symbols to CoinGecko IDs
2. Fetches detail (genesis_date, categories) and market data
3. Updates collected_tokens.json with correct data
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PROCESSED_DIR, RAW_DIR
from src.data_fetcher import CoinGeckoFetcher

# Manual mapping of Binance symbols to CoinGecko IDs
# Built from known tokens that didn't auto-match
KNOWN_MAP = {
    "SENT": "sentient",
    "KMNO": "kamino",
    "VELODROME": "velodrome-finance",
    "BNSOL": "binance-staked-sol",
    "EIGEN": "eigenlayer",
    "1MBABYDOGE": "baby-doge-coin",
    "RONIN": "ronin",
    "JTO": "jito-governance-token",
    "MOB": "mobilecoin",
    "BSW": "biswap",
    "APE": "apecoin",
    "ANC": "anchor-protocol",
    "IMX": "immutable-x",
    "UST": "terrausd",
    "HIGH": "highstreet",
    "MC": "merit-circle",
    "RNDR": "render-token",
    "AMP": "amp-token",
    "PLA": "playdapp",
    "RGT": "rari-governance-token",
    "BNX": "binaryx",
    "CHESS": "tranchess",
    "ALPACA": "alpaca-finance",
    "RAY": "raydium",
    "BOND": "barnbridge",
    "KLAY": "klay-token",
    "ERN": "ethernity-chain",
    "NU": "nucypher",
    "LPT": "livepeer",
    "MDX": "mdex",
    "AR": "arweave",
    "MIR": "mirror-protocol",
    "AUTO": "auto",
    "PERP": "perpetual-protocol",
    "LINA": "linear",
    "TVK": "terra-virtua-kolect",
    "UFT": "unilend-finance",
    "FXS": "frax-share",
    "1INCH": "1inch",
    "DF": "dforce-token",
    "COVER": "cover-protocol",
    "FRONT": "frontier-token",
    "FOR": "force-protocol",
    "CVP": "powerpool-concentrated-voting-power",
    "KP3R": "keep3rv1",
    "AKRO": "akropolis",
    "EASY": "easyfi",
    "COCOS": "cocos-bcx",
    "TUSDB": "true-usd",
    "BGBP": None,  # Binance GBP stablecoin, no CG listing
    "FTM": "fantom",
    "PAX": "paxos-standard",
    "GO": "gochain",
    "NAS": "nebulas",
}


def main():
    tokens_path = PROCESSED_DIR / "collected_tokens.json"
    tokens = json.loads(tokens_path.read_text())

    binance_tokens = [t for t in tokens if t["id"].startswith("binance-")]
    print(f"Found {len(binance_tokens)} tokens with binance- prefix IDs")

    with CoinGeckoFetcher() as cg:
        # Also fetch coin list from CoinGecko to find any we missed
        print("\nFetching CoinGecko coin list for symbol matching...")
        try:
            coin_list = cg._request("/coins/list", cache_key="coins_list")
            # Build symbol -> id map (prefer higher popularity, but we have no ranking here)
            sym_to_ids: dict[str, list[str]] = {}
            for coin in coin_list:
                sym = coin.get("symbol", "").upper()
                if sym:
                    sym_to_ids.setdefault(sym, []).append(coin["id"])
            print(f"  Loaded {len(coin_list)} coins from CoinGecko list")
        except Exception as e:
            print(f"  Warning: couldn't fetch coin list: {e}")
            sym_to_ids = {}

        # Also load cached market data for current price/rank
        cg_markets: dict[str, dict] = {}
        for page in range(1, 11):
            cache_path = RAW_DIR / f"markets_page_{page}.json"
            if cache_path.exists():
                for coin in json.loads(cache_path.read_text()):
                    cg_markets[coin["id"]] = coin

        updated = 0
        failed = []

        for t in binance_tokens:
            sym = t["symbol"].upper()
            # Normalize: strip 1000 prefix
            norm_sym = sym.lstrip("0123456789") if sym.startswith("1") else sym
            if sym.startswith("1000"):
                norm_sym = sym[4:]
            elif sym.startswith("1M"):
                norm_sym = sym  # Keep as-is for 1MBABYDOGE

            # Look up CoinGecko ID
            cg_id = KNOWN_MAP.get(sym) or KNOWN_MAP.get(norm_sym)

            # If not in known map, try the coin list
            if not cg_id and sym in sym_to_ids:
                candidates = sym_to_ids[sym]
                if len(candidates) == 1:
                    cg_id = candidates[0]
                else:
                    # Try to pick the best match by name similarity
                    name_lower = t["name"].lower()
                    for candidate in candidates:
                        if name_lower in candidate or candidate in name_lower:
                            cg_id = candidate
                            break
                    if not cg_id:
                        cg_id = candidates[0]  # Fallback to first

            if not cg_id:
                print(f"  SKIP {sym} ({t['name']}) - no CoinGecko match")
                failed.append(sym)
                continue

            print(f"  {sym:12s} -> {cg_id}")

            # Fetch detail
            try:
                detail = cg.get_token_detail(cg_id)
                categories = detail.get("categories") or []

                # Check genesis_date
                raw_genesis = detail.get("genesis_date")
                old_launch = t["launch_date"]
                if raw_genesis:
                    try:
                        genesis = date.fromisoformat(raw_genesis)
                        listing_d = date.fromisoformat(old_launch)
                        if genesis < listing_d:
                            print(f"    Genesis {raw_genesis} earlier than listing {old_launch}")
                            t["launch_date"] = raw_genesis
                            t["launch_source"] = "coingecko_genesis"
                    except (ValueError, TypeError):
                        pass

                # Update categories
                if categories:
                    from src.binance_collector import _classify_category
                    t["categories"] = categories
                    t["category"] = _classify_category(categories, symbol=t["symbol"])

                # Update ID
                t["id"] = cg_id

            except Exception as e:
                print(f"    Warning: detail fetch failed for {cg_id}: {e}")
                # Still update the ID even if detail fails
                t["id"] = cg_id

            # Fetch market chart for launch price (if we don't have one)
            if t.get("launch_price") is None:
                try:
                    chart = cg.get_market_chart(cg_id)
                    prices = chart.get("prices", [])
                    if prices:
                        from src.binance_collector import _price_at_date
                        launch_d = date.fromisoformat(t["launch_date"])
                        t["launch_price"] = _price_at_date(prices, launch_d)
                except Exception as e:
                    print(f"    Warning: chart fetch failed for {cg_id}: {e}")

            # Update market data from cached markets
            market_info = cg_markets.get(cg_id)
            if market_info:
                t["current_price"] = market_info.get("current_price")
                t["market_cap"] = market_info.get("market_cap")
                t["market_cap_rank"] = market_info.get("market_cap_rank")
                t["ath"] = market_info.get("ath")
                t["atl"] = market_info.get("atl")
                t["image"] = market_info.get("image")

            updated += 1

        # Save updated tokens
        tokens_path.write_text(json.dumps(tokens, indent=2))
        print(f"\nUpdated {updated} tokens, {len(failed)} failed")
        if failed:
            print(f"  Failed: {', '.join(failed)}")

        # Summary of launch date changes
        genesis_count = sum(1 for t in tokens if t.get("launch_source") == "coingecko_genesis")
        binance_prefix_remaining = sum(1 for t in tokens if t["id"].startswith("binance-"))
        print(f"  Tokens using genesis_date as launch: {genesis_count}")
        print(f"  Tokens still with binance- prefix: {binance_prefix_remaining}")


if __name__ == "__main__":
    main()
