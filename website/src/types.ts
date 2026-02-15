export interface Token {
  id: string;
  symbol: string;
  name: string;
  current_price: number | null;
  market_cap: number | null;
  market_cap_rank: number | null;
  ath: number | null;
  atl: number | null;
  image: string | null;
  launch_date: string | null;
  launch_price: number | null;
  launch_market_cap: number | null;
  total_supply: number | null;
  launch_source: string | null;
  categories: string[];
  category: string | null;
  cycle_name: string | null;
  cycle_type: string | null;
  age_days: number | null;
  roi_since_launch: number | null;
  annualized_roi: number | null;
  roi_vs_btc: number | null;
  drawdown_from_ath: number | null;
  binance_listed?: boolean;
  binance_delisted?: boolean;
  binance_delist_date?: string | null;
}

export interface SummaryStats {
  total_tokens: number;
  tokens_with_launch_date: number;
  tokens_by_cycle_type: Record<string, number>;
  median_roi_by_cycle_type: Record<string, number | null>;
  median_annualized_roi_by_cycle_type: Record<string, number | null>;
  median_roi_vs_btc_by_cycle_type: Record<string, number | null>;
  fraction_currently_top100_by_cycle_type: Record<string, number | null>;
  median_drawdown_by_cycle_type: Record<string, number | null>;
  delist_rate_by_cycle_type?: Record<string, number | null>;
  best_performers: PerformerSummary[];
  worst_performers: PerformerSummary[];

  // Mann-Whitney U test: Bull vs Bear annualized ROI
  bull_vs_bear_mannwhitney_pvalue: number | null;
  bull_vs_bear_effect_size: number | null;
  bull_vs_bear_median_diff: number | null;
  bull_vs_bear_ci_lower: number | null;
  bull_vs_bear_ci_upper: number | null;
  bull_n: number | null;
  bear_n: number | null;

  // BTC-relative tests
  btc_rel_mannwhitney_pvalue: number | null;
  btc_rel_effect_size: number | null;
  btc_rel_median_diff: number | null;
  btc_rel_ci_lower: number | null;
  btc_rel_ci_upper: number | null;

  // Transparency counts
  tokens_excluded_stablecoin: number;
  tokens_excluded_wrapped: number;
  tokens_imputed_dead: number;
}

export interface PerformerSummary {
  id: string;
  symbol: string;
  name: string;
  cycle_type: string | null;
  cycle_name: string | null;
  annualized_roi: number | null;
  roi_since_launch: number | null;
  roi_vs_btc: number | null;
  market_cap_rank: number | null;
  binance_delisted?: boolean;
}

export interface MarketCycle {
  name: string;
  start: string | null;
  end: string | null;
  type: string;
}

export interface SensitivityResult {
  shift_months: number;
  pvalue: number | null;
  effect_size: number | null;
  bull_n: number;
  bear_n: number;
  significant: boolean;
}

// BTC history is [timestamp_ms, price][]
export type BTCHistory = [number, number][];
