#!/usr/bin/env python3
"""Generate realistic sample data for website development/testing."""
import json
import random
import math
import sys
from datetime import date, timedelta
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from src.config import PROCESSED_DIR, WEBSITE_DATA_DIR
from src.market_cycles import get_cycle_name, get_cycle_type, get_all_cycles
from src.metrics import compute_metrics
from src.analyzer import compute_summary
from src.exporter import export_for_website

random.seed(42)

# Realistic top tokens with approximate data
SAMPLE_TOKENS = [
    # Early era
    ("bitcoin", "btc", "Bitcoin", "2009-01-03", "L1"),
    ("litecoin", "ltc", "Litecoin", "2011-10-07", "L1"),
    ("ripple", "xrp", "XRP", "2012-06-01", "L1"),
    # 2013 bull
    ("dogecoin", "doge", "Dogecoin", "2013-12-06", "Meme"),
    # 2014-2015 bear
    ("ethereum", "eth", "Ethereum", "2015-07-30", "L1"),
    ("tether", "usdt", "Tether", "2014-10-06", "Stablecoin"),
    ("stellar", "xlm", "Stellar", "2014-07-31", "L1"),
    ("monero", "xmr", "Monero", "2014-04-18", "L1"),
    ("dash", "dash", "Dash", "2014-01-18", "L1"),
    # 2016-2017 bull
    ("eos", "eos", "EOS", "2017-07-01", "L1"),
    ("cardano", "ada", "Cardano", "2017-10-01", "L1"),
    ("tron", "trx", "TRON", "2017-09-13", "L1"),
    ("neo", "neo", "NEO", "2016-10-17", "L1"),
    ("iota", "iota", "IOTA", "2017-06-13", "Infrastructure"),
    ("binancecoin", "bnb", "BNB", "2017-07-25", "Exchange"),
    ("chainlink", "link", "Chainlink", "2017-09-19", "Infrastructure"),
    ("vechain", "vet", "VeChain", "2017-08-22", "L1"),
    ("aave", "aave", "Aave", "2017-11-29", "DeFi"),
    ("cosmos", "atom", "Cosmos", "2017-04-06", "L1"),
    ("filecoin", "fil", "Filecoin", "2017-12-14", "AI/Storage"),
    # 2018-2019 bear
    ("polygon", "matic", "Polygon", "2018-04-29", "L2"),
    ("hedera", "hbar", "Hedera", "2018-03-13", "L1"),
    ("the-graph", "grt", "The Graph", "2018-07-26", "Infrastructure"),
    ("quant-network", "qnt", "Quant", "2018-06-25", "Infrastructure"),
    # 2019-2020 recovery
    ("solana", "sol", "Solana", "2020-01-10", "L1"),
    ("polkadot", "dot", "Polkadot", "2020-01-11", "L1"),
    ("avalanche-2", "avax", "Avalanche", "2020-01-15", "L1"),
    ("uniswap", "uni", "Uniswap", "2020-01-16", "DeFi"),
    ("algorand", "algo", "Algorand", "2019-06-19", "L1"),
    ("elrond", "egld", "MultiversX", "2019-09-04", "L1"),
    ("near", "near", "NEAR Protocol", "2020-02-12", "L1"),
    ("fantom", "ftm", "Fantom", "2019-06-29", "L1"),
    ("injective-protocol", "inj", "Injective", "2020-02-18", "DeFi"),
    # 2020-2021 bull
    ("shiba-inu", "shib", "Shiba Inu", "2020-08-01", "Meme"),
    ("terra-luna", "luna", "Terra", "2020-08-01", "L1"),
    ("axie-infinity", "axs", "Axie Infinity", "2020-11-06", "Gaming/NFT"),
    ("decentraland", "mana", "Decentraland", "2020-10-29", "Gaming/NFT"),
    ("sandbox", "sand", "The Sandbox", "2020-11-05", "Gaming/NFT"),
    ("pancakeswap-token", "cake", "PancakeSwap", "2020-09-28", "DeFi"),
    ("render-token", "rndr", "Render", "2020-06-10", "AI/Storage"),
    ("internet-computer", "icp", "Internet Computer", "2021-05-10", "L1"),
    ("flow", "flow", "Flow", "2021-01-27", "L1"),
    ("immutable-x", "imx", "Immutable", "2021-04-08", "L2"),
    ("gala", "gala", "Gala", "2020-09-16", "Gaming/NFT"),
    ("arweave", "ar", "Arweave", "2020-06-05", "AI/Storage"),
    ("lido-dao", "ldo", "Lido DAO", "2021-01-05", "DeFi"),
    ("arbitrum", "arb", "Arbitrum", "2021-08-31", "L2"),
    ("optimism", "op", "Optimism", "2021-06-01", "L2"),
    ("starknet", "strk", "Starknet", "2021-08-15", "L2"),
    # 2022 bear
    ("aptos", "apt", "Aptos", "2022-10-18", "L1"),
    ("sui", "sui", "Sui", "2022-03-22", "L1"),
    ("blur", "blur", "Blur", "2022-10-19", "DeFi"),
    ("worldcoin-wld", "wld", "Worldcoin", "2022-07-24", "Infrastructure"),
    # 2023 recovery
    ("celestia", "tia", "Celestia", "2023-01-15", "Infrastructure"),
    ("sei-network", "sei", "Sei", "2023-03-01", "L1"),
    ("pyth-network", "pyth", "Pyth Network", "2023-05-10", "Infrastructure"),
    ("jito-governance-token", "jto", "Jito", "2023-07-20", "DeFi"),
    # 2023-2025 bull
    ("jupiter-exchange", "jup", "Jupiter", "2024-01-31", "DeFi"),
    ("wormhole", "w", "Wormhole", "2024-04-03", "Infrastructure"),
    ("ethena", "ena", "Ethena", "2024-04-02", "DeFi"),
    ("eigen-layer", "eigen", "EigenLayer", "2024-05-01", "Infrastructure"),
    ("pepe", "pepe", "Pepe", "2023-11-14", "Meme"),
    ("bonk", "bonk", "Bonk", "2023-12-25", "Meme"),
    ("floki", "floki", "Floki", "2024-01-01", "Meme"),
    ("ondo-finance", "ondo", "Ondo Finance", "2024-01-18", "DeFi"),
]

# Fill to ~200 with random tokens
EXTRA_CATEGORIES = ["L1", "L2", "DeFi", "Infrastructure", "Gaming/NFT", "AI/Storage", "Meme", "Exchange", "Other"]
for i in range(200 - len(SAMPLE_TOKENS)):
    launch_year = random.choice([2015, 2016, 2017, 2017, 2017, 2018, 2018, 2019, 2020, 2020, 2021, 2021, 2021, 2022, 2023, 2024])
    launch_month = random.randint(1, 12)
    launch_day = random.randint(1, 28)
    cat = random.choice(EXTRA_CATEGORIES)
    name = f"Token{i+1}"
    SAMPLE_TOKENS.append((f"token-{i+1}", f"tk{i+1}", name, f"{launch_year}-{launch_month:02d}-{launch_day:02d}", cat))


def generate():
    tokens = []
    today = date(2026, 2, 13)

    for i, (id_, symbol, name, launch_str, category) in enumerate(SAMPLE_TOKENS):
        launch_date = date.fromisoformat(launch_str)
        age_days = (today - launch_date).days

        # Simulate realistic market data
        rank = i + 1

        # Higher-ranked tokens tend to have higher prices and market caps
        if id_ == "bitcoin":
            current_price = 97500.0
            market_cap = 1.93e12
            ath = 108000.0
            launch_price = 0.001
        elif id_ == "ethereum":
            current_price = 2700.0
            market_cap = 325e9
            ath = 4870.0
            launch_price = 0.31
        elif id_ == "tether":
            current_price = 1.0
            market_cap = 140e9
            ath = 1.05
            launch_price = 1.0
        elif id_ == "solana":
            current_price = 195.0
            market_cap = 95e9
            ath = 260.0
            launch_price = 0.22
        elif id_ == "binancecoin":
            current_price = 650.0
            market_cap = 95e9
            ath = 690.0
            launch_price = 0.10
        else:
            # Generate plausible prices based on rank
            base_mc = max(5e8, 2e12 * math.exp(-rank / 15))
            market_cap = base_mc * random.uniform(0.7, 1.3)
            current_price = market_cap / (random.uniform(1e8, 1e10))
            ath_mult = random.uniform(1.5, 20.0) if category != "Stablecoin" else 1.05
            ath = current_price * ath_mult

            # Launch price: earlier = cheaper
            if age_days > 3000:
                launch_price = current_price / random.uniform(50, 5000)
            elif age_days > 1500:
                launch_price = current_price / random.uniform(5, 200)
            elif age_days > 500:
                launch_price = current_price / random.uniform(1, 50)
            else:
                launch_price = current_price * random.uniform(0.3, 3.0)

        token = {
            "id": id_,
            "symbol": symbol,
            "name": name,
            "current_price": round(current_price, 6),
            "market_cap": round(market_cap),
            "market_cap_rank": rank,
            "ath": round(ath, 6),
            "atl": round(launch_price * random.uniform(0.1, 0.5), 8),
            "image": None,
            "launch_date": launch_str,
            "launch_price": round(launch_price, 8),
            "launch_source": "genesis_date",
            "categories": [category],
            "category": category,
        }
        tokens.append(token)

    # Generate BTC price history for charts
    btc_history = []
    btc_start = date(2013, 1, 1)
    btc_prices = {
        2013: (13, 1000), 2014: (1000, 310), 2015: (310, 430),
        2016: (430, 960), 2017: (960, 14000), 2018: (14000, 3700),
        2019: (3700, 7200), 2020: (7200, 29000), 2021: (29000, 47000),
        2022: (47000, 16500), 2023: (16500, 42000), 2024: (42000, 97000),
        2025: (97000, 97500), 2026: (97500, 97500),
    }
    for year, (start_p, end_p) in btc_prices.items():
        for month in range(1, 13):
            if year == 2026 and month > 2:
                break
            try:
                d = date(year, month, 15)
            except ValueError:
                continue
            frac = (month - 1) / 12
            price = start_p + (end_p - start_p) * frac
            # Add some noise
            price *= random.uniform(0.85, 1.15)
            ts = int(d.strftime("%s")) * 1000
            btc_history.append([ts, round(price, 2)])

    # Save BTC chart for metrics computation
    btc_chart = {"prices": [[ts, p] for ts, p in btc_history]}
    btc_chart_path = PROCESSED_DIR / "btc_chart.json"
    btc_chart_path.write_text(json.dumps(btc_chart))

    # Save collected tokens
    out_path = PROCESSED_DIR / "collected_tokens.json"
    out_path.write_text(json.dumps(tokens, indent=2))

    # Compute metrics
    tokens = compute_metrics(tokens, today=today)
    summary = compute_summary(tokens)

    # Export for website
    export_for_website(tokens, summary)

    # Print key findings
    print(f"\nGenerated {len(tokens)} sample tokens")
    print(f"Tokens by cycle type: {summary.tokens_by_cycle_type}")
    print(f"Median ann. ROI by cycle: {summary.median_annualized_roi_by_cycle_type}")


if __name__ == "__main__":
    generate()
