import json
import time
import httpx
from pathlib import Path
from typing import Any, Optional

from .config import COINGECKO_API_KEY, COINGECKO_PRO_BASE, RAW_DIR, RATE_LIMIT_DELAY


COINGECKO_FREE_BASE = "https://api.coingecko.com/api/v3"
FREE_RATE_LIMIT_DELAY = 6.5  # Free tier: ~10-30 calls/min, be conservative


class CoinGeckoFetcher:
    """CoinGecko API client with rate limiting and file-based caching."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.api_key = COINGECKO_API_KEY
        self.use_pro = bool(self.api_key)
        self.base_url = COINGECKO_PRO_BASE if self.use_pro else COINGECKO_FREE_BASE
        self.rate_delay = RATE_LIMIT_DELAY if self.use_pro else FREE_RATE_LIMIT_DELAY
        self.cache_dir = cache_dir or RAW_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0.0

        headers = {}
        if self.use_pro:
            headers["x-cg-pro-api-key"] = self.api_key
        self.client = httpx.Client(timeout=30.0, headers=headers)

        tier = "Pro" if self.use_pro else "Free (slower)"
        print(f"CoinGecko API: using {tier} tier ({self.base_url})")

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, key: str) -> Path:
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("?", "_").replace("&", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _get_cached(self, key: str) -> Optional[Any]:
        path = self._cache_path(key)
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _set_cache(self, key: str, data: Any):
        path = self._cache_path(key)
        path.write_text(json.dumps(data))

    def _request(self, endpoint: str, params: Optional[dict] = None, cache_key: Optional[str] = None) -> Any:
        key = cache_key or endpoint
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        max_retries = 5
        for attempt in range(max_retries):
            self._rate_limit()
            url = f"{self.base_url}{endpoint}"
            resp = self.client.get(url, params=params)
            if resp.status_code == 429:
                wait = min(30, 2 ** attempt * 5)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            self._set_cache(key, data)
            return data

        raise RuntimeError(f"Failed after {max_retries} retries: {endpoint}")

    def get_top_tokens(self, n: int = 200) -> list[dict]:
        """Fetch top N tokens by market cap. CoinGecko returns max 250 per page."""
        all_tokens = []
        per_page = min(n, 250)
        pages = (n + per_page - 1) // per_page

        for page in range(1, pages + 1):
            data = self._request(
                "/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": per_page,
                    "page": page,
                    "sparkline": "false",
                },
                cache_key=f"markets_page_{page}",
            )
            all_tokens.extend(data)

        return all_tokens[:n]

    def get_token_detail(self, coin_id: str) -> dict:
        """Fetch token detail including genesis_date and categories."""
        return self._request(
            f"/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "false",
                "community_data": "false",
                "developer_data": "false",
            },
            cache_key=f"detail_{coin_id}",
        )

    def get_market_chart(self, coin_id: str) -> dict:
        """Fetch full price history for a token."""
        return self._request(
            f"/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": "max"},
            cache_key=f"chart_{coin_id}",
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
