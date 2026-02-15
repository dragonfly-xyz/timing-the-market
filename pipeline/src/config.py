import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
WEBSITE_DATA_DIR = PROJECT_ROOT.parent / "website" / "public" / "data"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR, WEBSITE_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# CoinGecko API
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
COINGECKO_PRO_BASE = "https://pro-api.coingecko.com/api/v3"

# Collection settings
TOP_N_TOKENS = 200
RATE_LIMIT_DELAY = 0.15  # seconds between requests (Pro: 500/min)

# Stablecoin symbols for filtering (shared between collector and analyzer)
STABLECOIN_SYMBOLS = {
    "ust", "susd", "tusdb", "bgbp", "busd", "usdt", "usdc", "tusd", "dai",
    "fdusd", "usds", "usde", "usd1", "xusd", "rlusd", "gusd", "pax", "eurs",
}
