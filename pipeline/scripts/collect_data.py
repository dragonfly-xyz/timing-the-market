#!/usr/bin/env python3
"""Run data collection from CoinGecko API."""
import sys
import argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from src.data_fetcher import CoinGeckoFetcher
from src.data_collector import collect_all


def main():
    parser = argparse.ArgumentParser(description="Collect token data from CoinGecko")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tokens (e.g. 5 for testing)")
    args = parser.parse_args()

    with CoinGeckoFetcher() as fetcher:
        tokens = collect_all(fetcher, limit=args.limit)
    print(f"Done. Collected {len(tokens)} tokens.")


if __name__ == "__main__":
    main()
