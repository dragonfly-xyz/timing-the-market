# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Timing the Market is a data research project analyzing whether the timing of a cryptocurrency token's launch (bull vs bear market) impacts its long-term performance. It examines every token listed on Binance spot markets—including delisted ones—to avoid survivorship bias. Stablecoins and wrapped tokens are excluded. Dead tokens (delisted, no price data) are imputed as total losses. The verdict is data-driven (dynamic based on Mann-Whitney U test results).

Two main components:
- **`pipeline/`** — Python data collection & statistical analysis
- **`website/`** — Next.js 16 interactive data visualization

## Build & Run Commands

### Pipeline (Python)

```bash
# Activate virtualenv (from repo root)
source .venv/bin/activate

# Install dependencies
pip install -r pipeline/requirements.txt

# Run tests
pytest pipeline/tests/

# Run a single test
pytest pipeline/tests/test_metrics.py

# Collect data (preferred: Binance-based, no survivorship bias)
python pipeline/scripts/collect_binance.py

# Collect top-N tokens (faster, but has survivorship bias)
python pipeline/scripts/collect_data.py --limit 5

# Run analysis & export JSON to website/public/data/
python pipeline/scripts/run_analysis.py
```

### Website (Next.js / TypeScript)

```bash
cd website

# Install dependencies
npm install

# Dev server (http://localhost:3000)
npm run dev

# Production build (static export to website/out/)
npm run build

# Serve production build
npm run start
```

## Architecture

### Data Flow

```
Binance CMS API → collect_binance.py → CoinGecko API enrichment
    → pipeline/data/processed/*.json
    → run_analysis.py (metrics + stats)
    → website/public/data/*.json (tokens, summary_stats, market_cycles, btc_history, sensitivity)
    → next build (static site reads JSON at build time)
```

The pipeline exports JSON to `website/public/data/`, and the website imports it at build time via `website/src/data.ts`. There is no runtime API—the site is fully static.

### Pipeline (`pipeline/src/`)

| Module | Purpose |
|---|---|
| `config.py` | Paths, API URLs, constants |
| `models.py` | Pydantic data models (Token, MarketChart, etc.) |
| `market_cycles.py` | Hard-coded BTC market cycle definitions & date classification |
| `binance_fetcher.py` | Scrapes Binance CMS API for listing/delisting announcements |
| `binance_collector.py` | Main collection: Binance listings enriched with CoinGecko data |
| `data_fetcher.py` | CoinGecko API client with file-based caching & rate limiting |
| `data_collector.py` | Alternative: top-N by market cap (survivorship bias) |
| `metrics.py` | ROI, CAGR (365d min), drawdown_from_ath, geometric BTC-relative |
| `analyzer.py` | Filtering, dead token imputation, Mann-Whitney U, bootstrap CI, effect sizes, sensitivity analysis |
| `exporter.py` | NaN/Infinity sanitization, exports JSON + sensitivity.json |

### Website (`website/src/`)

- **App Router pages**: `app/page.tsx` (overview/verdict), `app/explorer/page.tsx` (token table), `app/analysis/page.tsx` (charts & stats), `app/methodology/page.tsx`
- **Charts** (`components/charts/`): Recharts-based — MarketCycleChart (BTC timeline + launch scatter), LaunchDistribution, ROIComparison, SurvivalRateChart
- **Tables** (`components/tables/TokenTable.tsx`): TanStack Table with sort/filter/pagination
- **Data layer**: `data.ts` imports JSON, `types.ts` defines TypeScript interfaces matching Python Pydantic models

### Key Design Decisions

- **Survivorship bias mitigation**: `collect_binance.py` is the preferred collector because it captures delisted tokens. `collect_data.py` only fetches current top tokens.
- **Data filtering**: Stablecoins and wrapped tokens excluded from analysis. Category classification priority: Stablecoin > Wrapped > Meme > L1 > L2 > DeFi > Exchange > Infrastructure > Gaming/NFT > AI/Storage > Other.
- **Genesis date preference**: CoinGecko `genesis_date` used as launch date when earlier than Binance listing (e.g. DOGE genesis 2013 vs Binance listing 2019). Manual CG_OVERRIDES dict for known symbol collisions.
- **Dead token imputation**: Delisted tokens without price data get roi_since_launch = -1.0 (total loss) to prevent silent exclusion from analysis.
- **Metric names**: `drawdown_from_ath` (not max_drawdown), `fraction_currently_top100` (not survival_rate), `median_drawdown` (not avg).
- **CAGR threshold**: Annualized ROI only computed for tokens >365 days old.
- **BTC-relative**: Geometric excess return `(1+token)/(1+btc)-1`, not arithmetic difference.
- **Statistical tests**: Mann-Whitney U only (no t-test). Bootstrap 95% CI for median difference. Rank-biserial effect size. Min 20 per group.
- **File-based API caching**: All CoinGecko responses cached in `pipeline/data/raw/` (gitignored) to avoid redundant requests and respect rate limits.
- **Shared schema**: Python Pydantic models and TypeScript interfaces must stay in sync (`models.py` ↔ `types.ts`).
- **Static site**: Website has no server-side data fetching. All data baked in at build time from `public/data/`.

## Environment

Requires a `.env` file at repo root with `COINGECKO_API_KEY`. See `.env.example`.

## Dragonfly Brand Style

The website follows the **Dragonfly** brand design language:
- **Background**: Pure black `#000000`, surfaces `#0a0a0a`
- **Text**: Dragonfly Grey `#F2F2F2`
- **Accent**: Dragon Blood Orange `#FA4C14`
- **Tertiary** (use sparingly): Pink `#EC39B6`, Blue `#5014FA`
- **Data colors**: Bull `#34d399` (green), Bear `#fb7185` (red), Neutral `#888888`, Early `#5014FA`
- **Typography**: Non Natural Grotesk (primary), Non Natural Mono (data/labels). Font files in `website/public/fonts/`.
- **Logo**: Dragonfly logomark + wordmark SVGs in `website/public/images/`.
- **Style principles**: No rounded corners on containers, sharp edges, uppercase monospace labels, dotted separators, generous whitespace, no gradients.

## Tech Stack

- **Pipeline**: Python 3.14+, httpx, pydantic, scipy, numpy, pytest, python-dotenv
- **Website**: Next.js 16, React 19, TypeScript, Recharts, TanStack Table, Tailwind CSS 4
