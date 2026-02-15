import type { Token, SummaryStats, MarketCycle, BTCHistory, SensitivityResult, MARobustnessResult } from "./types";
import tokensJson from "../public/data/tokens.json";
import summaryJson from "../public/data/summary_stats.json";
import cyclesJson from "../public/data/market_cycles.json";
import btcJson from "../public/data/btc_history.json";
import sensitivityJson from "../public/data/sensitivity.json";
import maRobustnessJson from "../public/data/ma_robustness.json";

export const tokens: Token[] = tokensJson as Token[];
export const summary: SummaryStats = summaryJson as SummaryStats;
export const cycles: MarketCycle[] = cyclesJson as MarketCycle[];
export const btcHistory: BTCHistory = btcJson as BTCHistory;
export const sensitivity: SensitivityResult[] = sensitivityJson as SensitivityResult[];
export const maRobustness: MARobustnessResult[] = maRobustnessJson as MARobustnessResult[];
