import { cycles } from "@/data";

const CYCLE_TYPE_COLORS: Record<string, string> = {
  Bull: "bg-bull/20 text-bull",
  Bear: "bg-bear/20 text-bear",
  Neutral: "bg-dim/20 text-dim",
  Early: "bg-dfly-blue/20 text-dfly-blue",
};

export default function MethodologyPage() {
  return (
    <div className="space-y-12 max-w-3xl">
      <div>
        <h1 className="font-primary text-3xl md:text-4xl font-bold tracking-[-1px]">
          Methodology
        </h1>
        <p className="text-dim mt-2">
          How we collected, classified, and analyzed the data.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">Data Source</h2>
        <p className="text-dim text-sm leading-relaxed">
          Token listing and delisting history comes from{" "}
          <a
            href="https://www.binance.com/en/support/announcement"
            className="text-accent underline underline-offset-2 hover:text-accent/80"
            target="_blank"
            rel="noopener noreferrer"
          >
            Binance announcements
          </a>
          , covering every token whose listing was announced on the blog. Each token is then
          enriched with current price data, market cap, ATH/ATL, and categories
          from the{" "}
          <a
            href="https://www.coingecko.com/en/api"
            className="text-accent underline underline-offset-2 hover:text-accent/80"
            target="_blank"
            rel="noopener noreferrer"
          >
            CoinGecko API
          </a>
          .
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">Data Filtering</h2>
        <p className="text-dim text-sm leading-relaxed">
          To avoid contaminating metrics, we exclude:
        </p>
        <ul className="space-y-1 text-sm text-dim list-disc pl-5">
          <li>
            <strong className="text-dfly-grey">Stablecoins</strong> (USDC,
            TUSD, FDUSD, etc.) &mdash; their price is pegged and ROI is
            meaningless
          </li>
          <li>
            <strong className="text-dfly-grey">Wrapped/staked tokens</strong>{" "}
            (WBTC, stETH, etc.) &mdash; they track another asset, not
            independent performance
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">
          Launch Date Determination
        </h2>
        <p className="text-dim text-sm leading-relaxed">
          Each token&apos;s launch date is determined by comparing the Binance
          listing announcement date with CoinGecko&apos;s{" "}
          <code className="text-accent/80 bg-surface px-1.5 py-0.5 text-xs font-mono">
            genesis_date
          </code>
          . If the genesis date is earlier than the Binance listing, we use it
          as the launch date (e.g. DOGE launched in 2013 but was listed on
          Binance in 2019). Otherwise, the Binance listing date is used.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">
          Dead Token Imputation
        </h2>
        <p className="text-dim text-sm leading-relaxed">
          Tokens that were delisted from Binance and have no current price data
          on CoinGecko are imputed with a &minus;100% ROI (total loss). Without
          this step, dead tokens would be silently excluded from statistical
          tests, biasing results upward. We do not impute annualized ROI for
          these tokens since their exact lifespan may be uncertain.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">
          Market Cycle Definitions
        </h2>
        <p className="text-dim text-sm leading-relaxed">
          Market cycles are defined based on widely-accepted historical BTC
          price peaks and troughs, aligned with halving cycles. These boundaries
          are approximate &mdash; reasonable people can disagree on exact dates.
          We include a sensitivity analysis that tests whether shifting
          boundaries by 1-2 months changes the conclusion.
        </p>
        <div className="overflow-x-auto bg-surface border border-edge">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge">
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Cycle
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Start
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  End
                </th>
                <th className="px-4 py-3 text-left text-faint font-mono text-xs uppercase">
                  Type
                </th>
              </tr>
            </thead>
            <tbody>
              {cycles.map((c) => (
                <tr
                  key={c.name}
                  className="border-b border-edge/30 hover:bg-raised transition-colors"
                >
                  <td className="px-4 py-3">{c.name}</td>
                  <td className="px-4 py-3 text-dim font-mono">{c.start ?? "\u2014"}</td>
                  <td className="px-4 py-3 text-dim font-mono">
                    {c.end ?? "Present"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-xs font-mono uppercase ${CYCLE_TYPE_COLORS[c.type] ?? "bg-raised text-dim"}`}
                    >
                      {c.type}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">Metrics</h2>
        <div className="space-y-3 text-sm text-dim">
          <div>
            <strong className="text-dfly-grey">ROI since launch</strong> &mdash;{" "}
            <code className="text-accent/80 bg-surface px-1.5 py-0.5 text-xs font-mono">
              (current_price - launch_price) / launch_price
            </code>
          </div>
          <div>
            <strong className="text-dfly-grey">Annualized ROI (CAGR)</strong> &mdash;
            ROI normalized by age in years, providing a fairer comparison across
            eras. Only computed for tokens older than 365 days to avoid
            misleading extrapolations.
          </div>
          <div>
            <strong className="text-dfly-grey">ROI vs BTC</strong> &mdash;
            Geometric excess return:{" "}
            <code className="text-accent/80 bg-surface px-1.5 py-0.5 text-xs font-mono">
              (1 + token_ROI) / (1 + BTC_ROI) - 1
            </code>
            . Positive means it outperformed Bitcoin over the same period.
          </div>
          <div>
            <strong className="text-dfly-grey">Drawdown from ATH</strong> &mdash;{" "}
            <code className="text-accent/80 bg-surface px-1.5 py-0.5 text-xs font-mono">
              (ATH - current) / ATH
            </code>
            . Shows how far the token has currently fallen from its all-time
            high. Clamped to 0 if current price exceeds ATH.
          </div>
          <div>
            <strong className="text-dfly-grey">
              Fraction currently in top 100
            </strong>{" "}
            &mdash; Percentage of tokens from a given cycle that are currently
            ranked in the top 100 by market cap.
          </div>
          <div>
            <strong className="text-dfly-grey">Delist rate</strong> &mdash;
            Fraction of tokens from a given cycle that were later removed from
            Binance.
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-primary text-xl font-bold">Statistical Tests</h2>
        <p className="text-dim text-sm leading-relaxed">
          We use the <strong className="text-dfly-grey">Mann-Whitney U test</strong>{" "}
          to compare annualized ROI and BTC-relative ROI distributions between
          Bull and Bear launched tokens. This is a non-parametric test that
          doesn&apos;t assume normally distributed data &mdash; appropriate for
          the heavy-tailed distributions typical of crypto returns.
        </p>
        <p className="text-dim text-sm leading-relaxed">
          We report <strong className="text-dfly-grey">rank-biserial correlation</strong>{" "}
          as an effect size measure and compute{" "}
          <strong className="text-dfly-grey">bootstrap 95% confidence intervals</strong>{" "}
          (10,000 resamples) for the difference in medians. A minimum of 20
          tokens per group is required for statistical tests.
        </p>
      </section>

      <section className="space-y-3 border border-accent/20 p-8">
        <h2 className="font-primary text-xl font-bold text-accent">
          Important Caveats
        </h2>
        <ul className="space-y-3 text-sm text-dim list-disc pl-5">
          <li>
            <strong className="text-dfly-grey">Incomplete delisting data</strong>
            : While we track Binance delistings, tokens that failed on other
            exchanges or never gained traction are not captured. Some
            survivorship bias remains.
          </li>
          <li>
            <strong className="text-dfly-grey">Age disparity</strong>: Tokens
            launched in earlier cycles have had more time to appreciate.
            Annualized ROI and BTC-relative metrics help normalize for this, but
            imperfectly.
          </li>
          <li>
            <strong className="text-dfly-grey">Sample sizes</strong>: Some
            cycles have fewer tokens. We require a minimum of 20 tokens per
            group for statistical tests and report sample sizes alongside all
            results.
          </li>
          <li>
            <strong className="text-dfly-grey">
              Cycle boundaries are approximate
            </strong>
            : Different analysts define bull/bear cycles differently. Our
            sensitivity analysis shows how results change under shifted
            boundaries.
          </li>
          <li>
            <strong className="text-dfly-grey">Dead token imputation</strong>:
            Delisted tokens without price data are imputed as total losses. This
            is a conservative assumption &mdash; some may have retained value on
            other exchanges.
          </li>
          <li>
            <strong className="text-dfly-grey">Not financial advice</strong>:
            This is an educational analysis. Past performance does not predict
            future results.
          </li>
        </ul>
      </section>
    </div>
  );
}
