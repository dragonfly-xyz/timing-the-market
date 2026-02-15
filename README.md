# Timing the Token Market

**Does launching a token in a bull market vs a bear market predict its long-term performance?**

No. There is no statistically significant difference.

Live site: [timing-tokens.dragonfly.xyz](https://timing-tokens.dragonfly.xyz) | Analysis date: February 2025

## Key Findings

- **202 tokens** analyzed from Binance blog listing announcements (including 18 delisted/dead tokens imputed as total losses)
- **p-value: 0.81** (Mann-Whitney U test, bull vs bear launched tokens) — well above the 0.05 significance threshold
- **Effect size: 0.03** (rank-biserial correlation) — negligible
- **95% CI for median difference: [-10.9%, +14.2%]** — straddles zero
- Median annualized ROI: **-57.3%** (bull-launched) vs **-59.8%** (bear-launched) — both terrible, no meaningful difference
- Result holds across all robustness checks:
  - Shifting cycle boundaries by +/- 1-2 months (sensitivity analysis)
  - Replacing hand-labeled cycles with BTC moving average regime classification (50/100/200/300-day SMA windows)
- **Anchoring analysis**: Bear tokens actually launched at somewhat higher median market caps — no evidence of persistent bull-market valuation premium
- 17 stablecoins and 6 wrapped tokens excluded from analysis

## Methodology

### Data Collection
- **Source**: Every token whose listing was announced on the Binance blog, scraped from Binance CMS API
- **Enrichment**: CoinGecko API for price history, market data, genesis dates, and categorization
- **Survivorship bias mitigation**: Includes delisted tokens (not just current top-N). Dead tokens (delisted, no price data) imputed as -100% ROI.
- **Launch date**: Uses CoinGecko genesis date when earlier than Binance listing (e.g., DOGE genesis 2013 vs Binance listing 2019)

### Market Cycle Definitions
| Cycle | Period | Type |
|-------|--------|------|
| 2013 Bull (Spring) | Jan 2013 - May 2013 | Bull |
| 2013 Correction | May 2013 - Oct 2013 | Neutral |
| 2013 Bull (Fall) | Oct 2013 - Jan 2014 | Bull |
| 2014-2015 Bear | Jan 2014 - Aug 2015 | Bear |
| 2015-2016 Recovery | Aug 2015 - Jan 2016 | Neutral |
| 2016-2017 Bull | Jan 2016 - Jan 2018 | Bull |
| 2018-2019 Bear | Jan 2018 - Dec 2018 | Bear |
| 2019-2020 Recovery | Dec 2018 - Mar 2020 | Neutral |
| 2020-2021 Bull | Mar 2020 - Nov 2021 | Bull |
| 2022 Bear | Nov 2021 - Nov 2022 | Bear |
| 2023 Recovery | Nov 2022 - Oct 2023 | Neutral |
| 2023-2025 Bull | Oct 2023 - Nov 2025 | Bull |
| 2025-2026 Bear | Nov 2025 - present | Bear |

### Statistical Approach
- **Mann-Whitney U test** (non-parametric, no normality assumption)
- **Bootstrap 95% confidence interval** for median difference (10,000 iterations)
- **Rank-biserial effect size** for practical magnitude
- **Sensitivity analysis** with shifted cycle boundaries (+/- 1-2 months)
- **MA robustness check**: BTC N-day SMA regime classification (50/100/200/300-day windows) as alternative to hand-labeled cycles
- **Anchoring analysis**: Compares launch-day market caps, FDV proxies, and current market caps between groups
- **Minimum 20 tokens per group** required for testing
- **Annualized ROI (CAGR)** only computed for tokens > 365 days old
- **BTC-relative ROI**: Geometric excess return `(1+token)/(1+btc)-1`

### Exclusions
- Stablecoins (USDT, USDC, DAI, etc.) — by CoinGecko category + symbol-based override
- Wrapped/bridged tokens (WBTC, stETH, etc.)
- Tokens with < 365 days of history excluded from annualized metrics

## Project Structure

```
pipeline/          Python data collection & statistical analysis
  src/             Core modules (fetchers, metrics, analyzer, exporter)
  scripts/         CLI scripts (collect_binance.py, run_analysis.py)
  data/            Raw API cache + processed data (gitignored)
  tests/           pytest test suite

website/           Next.js static site for data visualization
  src/app/         App Router pages (overview, analysis, methodology, explorer)
  src/components/  Charts (Recharts) and tables (TanStack Table)
  public/data/     Exported JSON consumed at build time
```

## Running Locally

### Pipeline
```bash
source .venv/bin/activate
pip install -r pipeline/requirements.txt

# Collect data (requires COINGECKO_API_KEY in .env)
python pipeline/scripts/collect_binance.py
python pipeline/scripts/run_analysis.py
```

### Website
```bash
cd website
npm install
npm run dev       # http://localhost:3000
npm run build     # Static export to website/out/
```

## Tech Stack

- **Pipeline**: Python 3.14+, httpx, pydantic, scipy, numpy, pytest
- **Website**: Next.js 16, React 19, TypeScript, Recharts, TanStack Table, Tailwind CSS 4
- **Brand**: Dragonfly design system (Non Natural Grotesk, dark theme, Dragon Blood Orange accents)

## Credits

Built with [Claude Code](https://claude.ai/code). Research by [Haseeb Qureshi](https://github.com/Haseeb-Qureshi).
