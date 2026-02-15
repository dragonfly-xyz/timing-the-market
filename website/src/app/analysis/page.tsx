import { tokens, summary, sensitivity } from "@/data";
import ROIComparison from "@/components/charts/ROIComparison";
import SurvivalRateChart from "@/components/charts/SurvivalRateChart";

const CYCLE_TYPE_COLORS: Record<string, string> = {
  Bull: "text-bull",
  Bear: "text-bear",
  Neutral: "text-dim",
  Early: "text-dfly-blue",
};

function fmtPct(n: number | null | undefined): string {
  if (n == null) return "\u2014";
  return `${(n * 100).toFixed(1)}%`;
}

function fmtUsd(n: number): string {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function median(arr: number[]): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

function effectSizeLabel(r: number | null | undefined): string {
  if (r == null) return "\u2014";
  const abs = Math.abs(r);
  if (abs < 0.1) return "negligible";
  if (abs < 0.3) return "small";
  if (abs < 0.5) return "medium";
  return "large";
}

function computeAnchoringStats() {
  const bull = tokens.filter(
    (t) => t.cycle_type === "Bull" && t.market_cap != null
  );
  const bear = tokens.filter(
    (t) => t.cycle_type === "Bear" && t.market_cap != null
  );

  const bullMcaps = bull.map((t) => t.market_cap!);
  const bearMcaps = bear.map((t) => t.market_cap!);

  const bullRanks = bull
    .filter((t) => t.market_cap_rank != null)
    .map((t) => t.market_cap_rank!);
  const bearRanks = bear
    .filter((t) => t.market_cap_rank != null)
    .map((t) => t.market_cap_rank!);

  return {
    bullMedianMcap: median(bullMcaps),
    bearMedianMcap: median(bearMcaps),
    bullMedianRank: median(bullRanks),
    bearMedianRank: median(bearRanks),
    bullN: bullMcaps.length,
    bearN: bearMcaps.length,
  };
}

export default function AnalysisPage() {
  const anchoring = computeAnchoringStats();
  return (
    <div className="space-y-16">
      <div>
        <h1 className="font-primary text-3xl md:text-4xl font-bold tracking-[-1px]">
          Detailed Analysis
        </h1>
        <p className="text-dim mt-2">
          Statistical comparisons of tokens launched during different market
          cycles.
        </p>
      </div>

      {/* ROI Comparison */}
      <section>
        <h2 className="font-primary text-2xl font-bold tracking-[-1px] mb-6">
          Annualized ROI by Launch Cycle
        </h2>
        <div className="bg-surface border border-edge p-4 md:p-6">
          <ROIComparison
            tokens={tokens}
            summaryMedians={summary.median_annualized_roi_by_cycle_type}
          />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3">
          {(["Bull", "Bear"] as const).map((ct) => {
            const v = summary.median_annualized_roi_by_cycle_type[ct];
            return (
              <div key={ct} className="bg-surface border border-edge p-4">
                <p className="text-dim text-sm">
                  <span className={CYCLE_TYPE_COLORS[ct]}>{ct}</span> median ann. ROI
                </p>
                <p className={`font-mono font-bold text-lg mt-1 ${v != null && v >= 0 ? "text-bull" : "text-bear"}`}>
                  {fmtPct(v)}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Fraction in Top 100 */}
      <section>
        <h2 className="font-primary text-2xl font-bold tracking-[-1px] mb-2">
          Fraction Currently in Top 100
        </h2>
        <p className="text-dim text-sm mb-6">
          Percentage of tokens from each cycle still in the top 100 by market
          cap today.
        </p>
        <div className="bg-surface border border-edge p-4 md:p-6">
          <SurvivalRateChart summary={summary} />
        </div>
      </section>

      {/* Statistical tests */}
      {summary.bull_vs_bear_mannwhitney_pvalue != null && (
        <section className="bg-surface border border-edge p-8">
          <h2 className="font-primary text-xl font-bold tracking-[-1px] mb-3">
            Statistical Tests
          </h2>
          <p className="text-dim text-sm mb-6">
            Comparing Bull vs Bear launched tokens using Mann-Whitney U test
            (non-parametric, no normality assumption).
          </p>

          {/* Annualized ROI */}
          <div className="mb-8">
            <p className="font-mono text-faint text-xs uppercase tracking-[0.15em] mb-4">
              Annualized ROI
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-faint text-xs font-mono uppercase">p-value</p>
                <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                  {summary.bull_vs_bear_mannwhitney_pvalue.toFixed(4)}
                </p>
              </div>
              {summary.bull_vs_bear_effect_size != null && (
                <div>
                  <p className="text-faint text-xs font-mono uppercase">effect size</p>
                  <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                    {summary.bull_vs_bear_effect_size.toFixed(3)}
                  </p>
                  <p className="text-faint text-xs mt-0.5">
                    {effectSizeLabel(summary.bull_vs_bear_effect_size)}
                  </p>
                </div>
              )}
              {summary.bull_vs_bear_ci_lower != null &&
                summary.bull_vs_bear_ci_upper != null && (
                  <div>
                    <p className="text-faint text-xs font-mono uppercase">95% CI (median diff)</p>
                    <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                      [{fmtPct(summary.bull_vs_bear_ci_lower)},{" "}
                      {fmtPct(summary.bull_vs_bear_ci_upper)}]
                    </p>
                  </div>
                )}
              <div>
                <p className="text-faint text-xs font-mono uppercase">sample sizes</p>
                <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                  {summary.bull_n} / {summary.bear_n}
                </p>
                <p className="text-faint text-xs mt-0.5">bull / bear</p>
              </div>
            </div>
          </div>

          {/* BTC-relative */}
          {summary.btc_rel_mannwhitney_pvalue != null && (
            <div className="border-t border-edge pt-6">
              <p className="font-mono text-faint text-xs uppercase tracking-[0.15em] mb-4">
                ROI vs BTC (Geometric Excess Return)
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-faint text-xs font-mono uppercase">p-value</p>
                  <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                    {summary.btc_rel_mannwhitney_pvalue.toFixed(4)}
                  </p>
                </div>
                {summary.btc_rel_effect_size != null && (
                  <div>
                    <p className="text-faint text-xs font-mono uppercase">effect size</p>
                    <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                      {summary.btc_rel_effect_size.toFixed(3)}
                    </p>
                    <p className="text-faint text-xs mt-0.5">
                      {effectSizeLabel(summary.btc_rel_effect_size)}
                    </p>
                  </div>
                )}
                {summary.btc_rel_ci_lower != null &&
                  summary.btc_rel_ci_upper != null && (
                    <div>
                      <p className="text-faint text-xs font-mono uppercase">95% CI (median diff)</p>
                      <p className="font-mono text-lg font-bold mt-1 text-dfly-grey">
                        [{fmtPct(summary.btc_rel_ci_lower)},{" "}
                        {fmtPct(summary.btc_rel_ci_upper)}]
                      </p>
                    </div>
                  )}
              </div>
            </div>
          )}

          <p className="text-faint text-xs mt-6 font-mono">
            p &lt; 0.05 suggests a statistically significant difference. Effect
            size (rank-biserial correlation) indicates practical magnitude.
          </p>
        </section>
      )}

      {/* Anchoring Analysis */}
      <section id="anchoring" className="bg-surface border border-edge p-8">
        <h2 className="font-primary text-xl font-bold tracking-[-1px] mb-3">
          Anchoring Analysis
        </h2>
        <p className="text-dim text-sm mb-2">
          A natural objection: if bull-market tokens launch at higher FDVs and
          ROI is equivalent, they would maintain higher absolute dollar
          valuations. Does the launch-day premium persist?
        </p>
        <p className="text-dim text-sm mb-6">
          We test this by comparing current market capitalizations and rankings
          between bull and bear groups. If anchoring holds, bull tokens should
          have significantly higher current market caps.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div>
            <p className="text-faint text-xs font-mono uppercase">
              Bull median market cap
            </p>
            <p className="font-mono text-lg font-bold mt-1 text-bull">
              {fmtUsd(anchoring.bullMedianMcap)}
            </p>
            <p className="text-faint text-xs mt-0.5">n={anchoring.bullN}</p>
          </div>
          <div>
            <p className="text-faint text-xs font-mono uppercase">
              Bear median market cap
            </p>
            <p className="font-mono text-lg font-bold mt-1 text-bear">
              {fmtUsd(anchoring.bearMedianMcap)}
            </p>
            <p className="text-faint text-xs mt-0.5">n={anchoring.bearN}</p>
          </div>
          <div>
            <p className="text-faint text-xs font-mono uppercase">
              Bull median rank
            </p>
            <p className="font-mono text-lg font-bold mt-1 text-bull">
              #{Math.round(anchoring.bullMedianRank)}
            </p>
          </div>
          <div>
            <p className="text-faint text-xs font-mono uppercase">
              Bear median rank
            </p>
            <p className="font-mono text-lg font-bold mt-1 text-bear">
              #{Math.round(anchoring.bearMedianRank)}
            </p>
          </div>
        </div>

        <p className="text-dim text-sm">
          Current market capitalizations and rankings show no significant
          difference between bull and bear groups. The anchoring hypothesis
          predicts bull tokens should have higher absolute valuations&mdash;they
          do not. This suggests that any launch-day FDV premium from bull-market
          conditions does not persist over time.
        </p>
        <p className="text-faint text-xs mt-4 font-mono">
          Caveat: launch-day FDV data is not available from CoinGecko to test
          the anchoring decomposition directly. Current market cap is the best
          available proxy for the endpoint of the anchoring hypothesis.
        </p>
      </section>

      {/* Sensitivity Analysis */}
      {sensitivity.length > 0 && (
        <section className="bg-surface border border-edge p-8">
          <h2 className="font-primary text-xl font-bold tracking-[-1px] mb-3">
            Sensitivity Analysis
          </h2>
          <p className="text-dim text-sm mb-4">
            Testing whether the conclusion changes when cycle boundaries are
            shifted by 1-2 months in either direction.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-edge">
                  <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                    Boundary Shift
                  </th>
                  <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                    p-value
                  </th>
                  <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                    Bull n
                  </th>
                  <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                    Bear n
                  </th>
                  <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                    Result
                  </th>
                </tr>
              </thead>
              <tbody>
                {sensitivity.map((s) => (
                  <tr
                    key={s.shift_months}
                    className={`border-b border-edge/30 ${s.shift_months === 0 ? "bg-raised" : ""}`}
                  >
                    <td className="px-4 py-3 font-mono">
                      {s.shift_months === 0
                        ? "Baseline"
                        : `${s.shift_months > 0 ? "+" : ""}${s.shift_months} months`}
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {s.pvalue != null ? s.pvalue.toFixed(4) : "\u2014"}
                    </td>
                    <td className="px-4 py-3 font-mono text-dim">{s.bull_n}</td>
                    <td className="px-4 py-3 font-mono text-dim">{s.bear_n}</td>
                    <td className="px-4 py-3">
                      {s.significant ? (
                        <span className="text-accent font-mono text-xs uppercase">
                          Significant
                        </span>
                      ) : (
                        <span className="text-faint font-mono text-xs uppercase">
                          Not significant
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Top Performers */}
      <section>
        <h2 className="font-primary text-2xl font-bold tracking-[-1px] mb-6">
          Top 10 by Annualized ROI
        </h2>
        <div className="overflow-x-auto bg-surface border border-edge">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge">
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Token
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Cycle
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Ann. ROI
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  ROI
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  vs BTC
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Rank
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.best_performers.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-edge/30 hover:bg-raised transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-dfly-grey">
                    {p.name}{" "}
                    <span className="text-xs text-faint font-mono uppercase">
                      {p.symbol}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-dim">{p.cycle_name}</td>
                  <td className="px-4 py-3 font-mono text-bull">
                    {fmtPct(p.annualized_roi)}
                  </td>
                  <td className={`px-4 py-3 font-mono ${(p.roi_since_launch ?? 0) >= 0 ? "text-bull" : "text-bear"}`}>
                    {fmtPct(p.roi_since_launch)}
                  </td>
                  <td className={`px-4 py-3 font-mono ${(p.roi_vs_btc ?? 0) >= 0 ? "text-bull" : "text-bear"}`}>
                    {fmtPct(p.roi_vs_btc)}
                  </td>
                  <td className="px-4 py-3 font-mono text-faint">
                    #{p.market_cap_rank}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
