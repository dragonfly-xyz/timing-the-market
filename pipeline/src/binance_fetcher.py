import json
import re
import time
import httpx
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional

from .config import RAW_DIR

BINANCE_CMS_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
PAGE_SIZE = 50
REQUEST_DELAY = 2.0  # seconds between requests to avoid WAF

# Catalog IDs
LISTING_CATALOG = 48
DELISTING_CATALOG = 161

# Primary pattern: extract everything after "Binance Will List" then parse name/symbol from it
LISTING_RE = re.compile(r"Binance Will List\s+(.+)", re.IGNORECASE)
# Extract "Name (SYMBOL)" — symbol is 1-10 uppercase alphanumeric chars inside parens
SYMBOL_RE = re.compile(r"^(.+?)\s*\(([A-Z0-9]{1,10})\)")
# Multiple tokens: "Binance Will List TokenA (A) and TokenB (B)"
MULTI_TOKEN_RE = re.compile(r"([^,&]+?\s*\([A-Z0-9]{1,10}\))")
# Early format: "TOKEN Market" (e.g., "OMG Market")
EARLY_RE = re.compile(r"^(\w+)\s+Market$")

# Patterns to exclude (not new token listings)
EXCLUDE_PATTERNS = [
    re.compile(r"Futures", re.IGNORECASE),
    re.compile(r"Margin", re.IGNORECASE),
    re.compile(r"Trading Pairs", re.IGNORECASE),
    re.compile(r"Trading Bots", re.IGNORECASE),
    re.compile(r"Buy Crypto|Convert|Earn", re.IGNORECASE),
    re.compile(r"Pre-Market", re.IGNORECASE),
    re.compile(r"Leveraged Tokens", re.IGNORECASE),
]

# Patterns for delistings
DELIST_PATTERNS = [
    re.compile(r"Removal of Spot Trading Pairs", re.IGNORECASE),
    re.compile(r"Binance Will Delist", re.IGNORECASE),
    re.compile(r"Notice of Removal.*Spot", re.IGNORECASE),
]


class BinanceFetcher:
    """Fetches Binance listing/delisting announcements from the CMS API."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = (cache_dir or RAW_DIR) / "binance"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0.0
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _get_cached(self, key: str):
        path = self._cache_path(key)
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _set_cache(self, key: str, data):
        path = self._cache_path(key)
        path.write_text(json.dumps(data))

    def _fetch_page(self, catalog_id: int, page: int) -> dict:
        cache_key = f"catalog_{catalog_id}_page_{page}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._rate_limit()
        resp = self.client.get(
            BINANCE_CMS_URL,
            params={
                "type": 1,
                "catalogId": catalog_id,
                "pageNo": page,
                "pageSize": PAGE_SIZE,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._set_cache(cache_key, data)
        return data

    def fetch_all_announcements(self, catalog_id: int) -> list[dict]:
        """Fetch all announcements for a given catalog. Returns list of article dicts."""
        print(f"Fetching catalog {catalog_id} page 1...")
        first = self._fetch_page(catalog_id, 1)
        catalogs = first.get("data", {}).get("catalogs", [])
        if not catalogs:
            return []

        catalog = catalogs[0]
        total = catalog.get("total", 0)
        articles = catalog.get("articles", [])
        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

        print(f"  Total: {total} articles across {total_pages} pages")

        for page in range(2, total_pages + 1):
            print(f"  Fetching page {page}/{total_pages}...")
            data = self._fetch_page(catalog_id, page)
            page_catalogs = data.get("data", {}).get("catalogs", [])
            if page_catalogs:
                articles.extend(page_catalogs[0].get("articles", []))

        return articles

    def get_listings(self) -> list[dict]:
        """Get all new spot token listing announcements, parsed into individual tokens."""
        articles = self.fetch_all_announcements(LISTING_CATALOG)
        listings = []
        seen_symbols = set()

        for art in articles:
            title = art.get("title", "")
            release_ms = art.get("releaseDate", 0)

            # Skip non-spot-listing announcements
            if any(p.search(title) for p in EXCLUDE_PATTERNS):
                continue

            listing_date = datetime.fromtimestamp(release_ms / 1000, tz=timezone.utc).date()

            # Try main pattern: "Binance Will List ..."
            m = LISTING_RE.search(title)
            if not m:
                # Try early format: "TOKEN Market"
                em = EARLY_RE.match(title.strip())
                if em:
                    sym = em.group(1).upper()
                    if sym not in seen_symbols:
                        seen_symbols.add(sym)
                        listings.append({
                            "title": title,
                            "token_name": sym,
                            "token_symbol": sym,
                            "listing_date": listing_date.isoformat(),
                            "release_ms": release_ms,
                            "article_code": art.get("code"),
                        })
                continue

            remainder = m.group(1).strip()
            # Clean suffixes
            remainder = re.sub(r"\s+with\s+Seed\s+Tag.*", "", remainder, flags=re.IGNORECASE)
            remainder = re.sub(r"\s+on\s+Binance.*", "", remainder, flags=re.IGNORECASE)
            remainder = re.sub(r"\s+and\s+Opens?\s+Deposit.*", "", remainder, flags=re.IGNORECASE)
            remainder = re.sub(r"\s+and\s+Introduce\s+.*", "", remainder, flags=re.IGNORECASE)
            remainder = remainder.strip()

            # Try to find multiple tokens: "TokenA (A) and TokenB (B)"
            # Also handles: "TokenA (A), TokenB (B) and TokenC (C)"
            multi = MULTI_TOKEN_RE.findall(remainder)
            if multi:
                for chunk in multi:
                    chunk = chunk.strip().lstrip(",").lstrip("and").strip()
                    sm = SYMBOL_RE.match(chunk)
                    if sm:
                        name = sm.group(1).strip()
                        sym = sm.group(2).upper()
                        if sym not in seen_symbols:
                            seen_symbols.add(sym)
                            listings.append({
                                "title": title,
                                "token_name": name,
                                "token_symbol": sym,
                                "listing_date": listing_date.isoformat(),
                                "release_ms": release_ms,
                                "article_code": art.get("code"),
                            })
            else:
                # Single token, maybe without parens
                sm = SYMBOL_RE.match(remainder)
                if sm:
                    name = sm.group(1).strip()
                    sym = sm.group(2).upper()
                else:
                    # No parens — use the whole thing
                    name = remainder
                    sym = None

                key = sym or name.upper()
                if key not in seen_symbols:
                    seen_symbols.add(key)
                    listings.append({
                        "title": title,
                        "token_name": name,
                        "token_symbol": sym,
                        "listing_date": listing_date.isoformat(),
                        "release_ms": release_ms,
                        "article_code": art.get("code"),
                    })

        return listings

    def get_delistings(self) -> list[dict]:
        """Get all delisting announcements, extracting individual token symbols."""
        articles = self.fetch_all_announcements(DELISTING_CATALOG)
        delistings = []

        # Pattern: "Binance Will Delist SYM1, SYM2, SYM3 on DATE"
        delist_tokens_re = re.compile(
            r"Binance Will Delist\s+(.+?)\s+on\s+\d{4}", re.IGNORECASE
        )

        for art in articles:
            title = art.get("title", "")
            release_ms = art.get("releaseDate", 0)
            delist_date = datetime.fromtimestamp(release_ms / 1000, tz=timezone.utc).date()

            # Skip futures/margin-only delistings
            if re.search(r"Futures|Margin|Perpetual", title, re.IGNORECASE):
                # Still include "Removal of Spot Trading Pairs" even if other keywords present
                if not re.search(r"Spot", title, re.IGNORECASE):
                    continue

            # Extract specific symbols from "Binance Will Delist X, Y, Z on DATE"
            m = delist_tokens_re.search(title)
            if m:
                symbols_str = m.group(1)
                symbols = [s.strip() for s in re.split(r"[,&]|\band\b", symbols_str) if s.strip()]
                for sym in symbols:
                    # Clean: might be "TOKEN (SYMBOL)" or just "SYMBOL"
                    sm = re.match(r"(?:.*\()?([\w]+)\)?$", sym.strip())
                    if sm:
                        delistings.append({
                            "token_symbol": sm.group(1).upper(),
                            "delist_date": delist_date.isoformat(),
                            "title": title,
                            "release_ms": release_ms,
                        })
            else:
                # Generic delisting announcement (pair removals, etc.)
                delistings.append({
                    "token_symbol": None,
                    "delist_date": delist_date.isoformat(),
                    "title": title,
                    "release_ms": release_ms,
                })

        return delistings

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
