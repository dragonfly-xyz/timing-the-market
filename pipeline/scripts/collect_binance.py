#!/usr/bin/env python3
"""Collect token data using Binance listing history + CoinGecko enrichment."""
import sys
import argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from src.binance_fetcher import BinanceFetcher
from src.data_fetcher import CoinGeckoFetcher
from src.binance_collector import collect_binance_tokens


def main():
    parser = argparse.ArgumentParser(description="Collect Binance-listed token data")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tokens (for testing)")
    args = parser.parse_args()

    with BinanceFetcher() as binance, CoinGeckoFetcher() as coingecko:
        tokens = collect_binance_tokens(binance, coingecko, limit=args.limit)
    print(f"\nDone. Collected {len(tokens)} tokens.")


if __name__ == "__main__":
    main()
