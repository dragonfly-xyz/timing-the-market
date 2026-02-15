import { tokens, summary, cycles, btcHistory } from "@/data";
import MarketCycleChart from "@/components/charts/MarketCycleChart";
import LaunchDistribution from "@/components/charts/LaunchDistribution";

function fmtPct(n: number | null | undefined): string {
  if (n == null) return "\u2014";
  return `${(n * 100).toFixed(1)}%`;
}

function effectSizeLabel(r: number | null | undefined): string {
  if (r == null) return "";
  const abs = Math.abs(r);
  if (abs < 0.1) return "negligible";
  if (abs < 0.3) return "small";
  if (abs < 0.5) return "medium";
  return "large";
}

export default function Home() {
  const bullAnnROI = summary.median_annualized_roi_by_cycle_type["Bull"];
  const bearAnnROI = summary.median_annualized_roi_by_cycle_type["Bear"];
  const bullDelist = summary.delist_rate_by_cycle_type?.["Bull"];
  const bearDelist = summary.delist_rate_by_cycle_type?.["Bear"];
  const tokensWithDate = tokens.filter((t) => t.launch_date);
  const delistedCount = tokens.filter((t) => t.binance_delisted).length;
  const tokensWithoutData = tokens.filter(
    (t) => t.roi_since_launch == null && t.current_price == null
  ).length;

  // Dynamic verdict based on actual statistical results
  const pValue = summary.bull_vs_bear_mannwhitney_pvalue;
  const isSignificant = pValue != null && pValue < 0.05;

  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="pt-8">
        <h1 className="font-primary text-5xl md:text-6xl font-bold leading-[0.9] tracking-[-2px] max-w-[680px]">
          Does it matter when you launch your token?
        </h1>
        <p className="text-dim text-lg mt-6 max-w-2xl leading-relaxed">
          An analysis of every token whose listing was announced on the Binance blog (
          {summary.total_tokens} tokens after filtering), comparing long-term
          performance by market cycle, including {delistedCount} that were
          later delisted.
        </p>
      </section>

      {/* Verdict */}
      <section className="bg-surface border border-edge p-8 md:p-10">
        <p className="font-mono text-dim text-sm uppercase tracking-[0.2em] mb-4">
          The Verdict
        </p>
        <p className="font-primary text-2xl md:text-3xl font-bold leading-snug tracking-[-1px]">
          {isSignificant
            ? "Yes, launch timing predicts long-term performance."
            : "No, launching in a bull vs bear market does not predict performance."}
        </p>
        <p className="text-dim mt-4 max-w-2xl leading-relaxed">
          {isSignificant
            ? "Bull and bear market tokens show a measurable difference in median performance, though effect size should be considered before drawing practical conclusions."
            : <>There is <strong className="text-dfly-grey">no statistically significant difference</strong> in performance between tokens launched in bull markets vs bear markets.</>}
        </p>
        <p className="text-dim mt-3 max-w-2xl leading-relaxed">
          {isSignificant
            ? null
            : "There may be other considerations in when you choose to launch your token: cost, exchange fees, marketing expenses, etc. But if anything, those likely cut against launching in a bull market, as they tend to be higher in bulls vs bears."}
        </p>
        <p className="text-dim mt-3 max-w-2xl leading-relaxed">
          {isSignificant
            ? null
            : "That said, if you are doing a token sale along with your launch, the inverse is true\u2014if you\u2019re actually selling tokens, then obviously a bull market is better for you."}
        </p>
        {pValue != null && (
          <div className="flex flex-wrap gap-6 mt-5 font-mono text-sm text-dfly-grey/70">
            <span>Mann-Whitney p = {pValue.toFixed(4)}</span>
            {summary.bull_vs_bear_effect_size != null && (
              <span>
                effect size = {summary.bull_vs_bear_effect_size.toFixed(3)} (
                {effectSizeLabel(summary.bull_vs_bear_effect_size)})
              </span>
            )}
            {summary.bull_vs_bear_ci_lower != null &&
              summary.bull_vs_bear_ci_upper != null && (
                <span>
                  95% CI [{fmtPct(summary.bull_vs_bear_ci_lower)},{" "}
                  {fmtPct(summary.bull_vs_bear_ci_upper)}]
                </span>
              )}
            {summary.bull_n != null && summary.bear_n != null && (
              <span>
                n: {summary.bull_n} bull, {summary.bear_n} bear
              </span>
            )}
          </div>
        )}
      </section>

      {/* Bull vs Bear comparison */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-bull/20 p-8 space-y-6">
            <p className="font-mono text-bull text-xs uppercase tracking-[0.15em]">
              Bull Market Launches
              {summary.bull_n != null && (
                <span className="text-faint ml-2">(n={summary.bull_n})</span>
              )}
            </p>
            {[
              { val: fmtPct(bullAnnROI), label: "median annualized ROI" },
              { val: fmtPct(bullDelist), label: "delist rate" },
            ].map(({ val, label }) => (
              <div key={label}>
                <p className="font-mono text-2xl md:text-3xl font-bold text-bull">
                  {val}
                </p>
                <p className="text-dim text-sm mt-1">{label}</p>
              </div>
            ))}
          </div>
          <div className="border border-bear/20 p-8 space-y-6">
            <p className="font-mono text-bear text-xs uppercase tracking-[0.15em]">
              Bear Market Launches
              {summary.bear_n != null && (
                <span className="text-faint ml-2">(n={summary.bear_n})</span>
              )}
            </p>
            {[
              { val: fmtPct(bearAnnROI), label: "median annualized ROI" },
              { val: fmtPct(bearDelist), label: "delist rate" },
            ].map(({ val, label }) => (
              <div key={label}>
                <p className="font-mono text-2xl md:text-3xl font-bold text-bear">
                  {val}
                </p>
                <p className="text-dim text-sm mt-1">{label}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-6 mt-4 font-mono text-xs text-faint">
          <span>{summary.total_tokens} tokens analyzed</span>
          <span>{summary.tokens_with_launch_date} with launch date</span>
        </div>
      </section>

      {/* BTC Chart */}
      <section>
        <h2 className="font-primary text-2xl md:text-[50px] md:leading-[0.9] md:tracking-[-1px] font-bold mb-6">
          Token Launches on the BTC Price Timeline
        </h2>
        <div className="bg-surface border border-edge p-4 md:p-6">
          <MarketCycleChart
            btcHistory={btcHistory}
            cycles={cycles}
            tokens={tokensWithDate}
          />
        </div>
      </section>

      {/* Distribution */}
      <section>
        <h2 className="font-primary text-2xl md:text-[50px] md:leading-[0.9] md:tracking-[-1px] font-bold mb-6">
          Launches Per Market Cycle
        </h2>
        <div className="bg-surface border border-edge p-4 md:p-6">
          <LaunchDistribution tokens={tokensWithDate} />
        </div>
      </section>

      {/* Methodology */}
      <section>
        <h2 className="font-primary text-2xl md:text-[50px] md:leading-[0.9] md:tracking-[-1px] font-bold mb-6">
          Methodology
        </h2>
        <div className="text-dim space-y-3 max-w-2xl leading-relaxed">
          <p>
            We collected every token whose listing was announced on the Binance blog, including those later delisted.
            Each token is classified by its launch date into a BTC market cycle (bull or bear) and its long-term
            annualized ROI is computed. Delisted tokens with no remaining price data are imputed as total losses
            to avoid survivorship bias.
          </p>
          <p>
            The primary test is a Mann-Whitney U (non-parametric) comparing annualized ROI between bull-launched
            and bear-launched tokens, with bootstrap confidence intervals and sensitivity analysis across
            shifted cycle boundaries.
          </p>
          <p>
            <a href="/methodology" className="text-accent hover:underline font-mono text-sm">
              Full methodology &rarr;
            </a>
          </p>
        </div>
      </section>

      {/* Key Limitations */}
      <section className="border border-accent/20 p-8">
        <p className="font-mono text-accent text-xs uppercase tracking-[0.15em] mb-4">
          Key Limitations
        </p>
        <ul className="space-y-2 text-sm text-dim list-disc pl-5">
          {tokensWithoutData > 0 && (
            <li>
              {tokensWithoutData} tokens ({((tokensWithoutData / summary.total_tokens) * 100).toFixed(0)}%) had insufficient price data for analysis
            </li>
          )}
          <li>Sample is primarily from 2017&ndash;2025 Binance listings</li>
          {(summary.tokens_excluded_stablecoin > 0 ||
            summary.tokens_excluded_wrapped > 0) && (
            <li>
              {summary.tokens_excluded_stablecoin} stablecoins and{" "}
              {summary.tokens_excluded_wrapped} wrapped tokens excluded
            </li>
          )}
          <li>Only tokens that reached Binance listing are included</li>
          {summary.tokens_imputed_dead > 0 && (
            <li>
              {summary.tokens_imputed_dead} delisted tokens imputed as total
              losses (no price data available)
            </li>
          )}
        </ul>
      </section>

      {/* Disclosures */}
      <section className="border-t border-edge pt-8">
        <p className="font-mono text-faint text-xs uppercase tracking-[0.15em] mb-4">
          Disclosures
        </p>
        <div className="space-y-3 text-xs text-faint leading-relaxed">
          <p>
            This report is for informational purposes only. It is not an offer, solicitation, or
            recommendation to buy or sell any securities, tokens, or digital assets, or to pursue
            any particular investment strategy. Nothing herein constitutes investment, legal, tax,
            or other professional advice. You should consult your own advisers before making any
            investment decisions.
          </p>
          <p>
            Dragonfly Digital Management, LLC (&ldquo;Dragonfly&rdquo;) is an SEC-registered
            investment adviser that holds positions in cryptocurrency and digital assets, including
            tokens that may be referenced in this analysis. Dragonfly is acting in its own financial
            interest and not necessarily in the interests of other token holders.
          </p>
          <p>
            There are no warranties, expressed or implied, as to the accuracy, completeness, or
            results obtained from any information provided herein. Information has been obtained from
            sources believed to be reliable, but neither Dragonfly nor its affiliates warrant the
            timeliness, accuracy, or completeness of this information. The information is subject to
            change without notice.
          </p>
          <p>
            Past performance is not indicative of future results. Any forward-looking statements
            reflect current views and involve risks and uncertainties that could cause actual results
            to differ materially.
          </p>
          <p>
            For additional information, see Dragonfly&rsquo;s{" "}
            <a
              href="https://www.dragonfly.xyz/legal/disclosures"
              target="_blank"
              rel="noopener noreferrer"
              className="text-dim hover:underline"
            >
              Disclosures
            </a>
            {" "}and{" "}
            <a
              href="https://www.dragonfly.xyz/legal/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="text-dim hover:underline"
            >
              Terms of Use
            </a>
            .
          </p>
        </div>
      </section>

      {/* Attribution */}
      <section className="text-center py-4">
        <p className="font-mono text-xs text-faint">
          Built with{" "}
          <a
            href="https://claude.ai/code"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Claude Code
          </a>
          , piloted by{" "}
          <a
            href="https://twitter.com/hosseeb"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Haseeb Qureshi
          </a>
          {" "}&middot;{" "}
          <a
            href="https://github.com/dragonfly-xyz/timing-the-market"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            View on GitHub
          </a>
        </p>
      </section>
    </div>
  );
}
