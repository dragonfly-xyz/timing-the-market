import type { Token, SummaryStats, MarketCycle, BTCHistory, SensitivityResult } from "./types";
import tokensJson from "../public/data/tokens.json";
import summaryJson from "../public/data/summary_stats.json";
import cyclesJson from "../public/data/market_cycles.json";
import btcJson from "../public/data/btc_history.json";
import sensitivityJson from "../public/data/sensitivity.json";

export const tokens: Token[] = tokensJson as Token[];
export const summary: SummaryStats = summaryJson as SummaryStats;
export const cycles: MarketCycle[] = cyclesJson as MarketCycle[];
export const btcHistory: BTCHistory = btcJson as BTCHistory;
export const sensitivity: SensitivityResult[] = sensitivityJson as SensitivityResult[];
