from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class TokenMarketData(BaseModel):
    """Raw market data from CoinGecko /coins/markets."""
    id: str
    symbol: str
    name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    market_cap_rank: Optional[int] = None
    ath: Optional[float] = None
    atl: Optional[float] = None
    image: Optional[str] = None


class TokenDetail(BaseModel):
    """Detail data from CoinGecko /coins/{id}."""
    id: str
    genesis_date: Optional[date] = None
    categories: list[str] = []
    description: str = ""


class TokenMetrics(BaseModel):
    """Computed metrics for a single token."""
    id: str
    symbol: str
    name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    market_cap_rank: Optional[int] = None
    ath: Optional[float] = None
    atl: Optional[float] = None
    image: Optional[str] = None

    # Launch info
    launch_date: Optional[str] = None  # ISO date string
    launch_price: Optional[float] = None
    launch_market_cap: Optional[float] = None
    total_supply: Optional[float] = None
    launch_source: Optional[str] = None  # "coingecko_genesis" or "binance_listing"

    # Cycle classification
    cycle_name: Optional[str] = None
    cycle_type: Optional[str] = None

    # Metrics
    age_days: Optional[int] = None
    roi_since_launch: Optional[float] = None
    annualized_roi: Optional[float] = None
    roi_vs_btc: Optional[float] = None
    drawdown_from_ath: Optional[float] = None

    # Category
    category: Optional[str] = None
    categories: list[str] = []

    # Binance status
    binance_listed: bool = False
    binance_delisted: bool = False
    binance_delist_date: Optional[str] = None


class SummaryStats(BaseModel):
    """Aggregate statistics for the website."""
    total_tokens: int
    tokens_with_launch_date: int
    tokens_by_cycle_type: dict[str, int]
    median_roi_by_cycle_type: dict[str, Optional[float]]
    median_annualized_roi_by_cycle_type: dict[str, Optional[float]]
    median_roi_vs_btc_by_cycle_type: dict[str, Optional[float]]
    fraction_currently_top100_by_cycle_type: dict[str, Optional[float]]
    median_drawdown_by_cycle_type: dict[str, Optional[float]]
    # Binance delist rate = fraction of tokens delisted from Binance (proxy for failure)
    delist_rate_by_cycle_type: dict[str, Optional[float]]
    best_performers: list[dict]
    worst_performers: list[dict]

    # Mann-Whitney U test: Bull vs Bear annualized ROI
    bull_vs_bear_mannwhitney_pvalue: Optional[float] = None
    bull_vs_bear_effect_size: Optional[float] = None  # rank-biserial correlation
    bull_vs_bear_median_diff: Optional[float] = None  # bull median - bear median
    bull_vs_bear_ci_lower: Optional[float] = None  # 95% CI lower bound
    bull_vs_bear_ci_upper: Optional[float] = None  # 95% CI upper bound
    bull_n: Optional[int] = None
    bear_n: Optional[int] = None

    # BTC-relative statistical tests
    btc_rel_mannwhitney_pvalue: Optional[float] = None
    btc_rel_effect_size: Optional[float] = None
    btc_rel_median_diff: Optional[float] = None
    btc_rel_ci_lower: Optional[float] = None
    btc_rel_ci_upper: Optional[float] = None

    # Transparency: how many tokens were excluded or imputed
    tokens_excluded_stablecoin: int = 0
    tokens_excluded_wrapped: int = 0
    tokens_imputed_dead: int = 0
