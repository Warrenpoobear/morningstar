# Wake Robin — Morningstar Benchmark Data Feed

A versioned, read-only **data feed** of 29 daily total-return benchmark series pulled from
Morningstar Direct. Other projects consume it through a small pandas accessor
(`morningstar_feed`) — not by hand-parsing CSVs — so the schema and identifier map stay in
one place.

- **Coverage:** 2016-07-01 → latest month-end · 29 benchmarks · USD · daily
- **As-of / freshness / SecId map:** `datasets.json` (machine-readable manifest)
- **Provenance, limitations, refresh:** `GOVERNANCE.md`
- **Refresh runbook / token notes:** `SKILL.md`

## Consume it from another project

Pick whichever wiring fits the consumer repo:

**A. Install as an editable package (recommended)**
```bash
pip install -e C:/Projects/morningstar     # or the WSL path /mnt/c/Projects/morningstar
```
```python
import morningstar_feed as mf
mf.trailing_return("S&P 500", "1Y")        # 22.32   (annualized for >1Y)
```

**B. No install — point at the checkout via env var**
```python
import os, sys
os.environ["MORNINGSTAR_FEED_DIR"] = r"C:\Projects\morningstar"
sys.path.insert(0, os.environ["MORNINGSTAR_FEED_DIR"])
import morningstar_feed as mf
```

**C. Git submodule** — vendor this repo under the consumer and import `morningstar_feed`.

`MORNINGSTAR_FEED_DIR` overrides where the CSVs are read from, so a consumer can pin a
specific snapshot without moving code.

## API

```python
mf.benchmark_names()                 # 29 canonical names
mf.list_benchmarks()                 # DataFrame: name, secid, start, end, rows
mf.resolve_name("xbi")               # 'State Street SPDR S&P Biotech ETF'  (aliases + SecIds)
mf.secid("US Agg")                   # 'FOUSA05Y32'

mf.get_series("S&P 500")             # Series of the TR index (kind='return_index'|'daily_return')
mf.load_return_index(["S&P 500","US Agg"], start="2024-01-01")   # wide DataFrame
mf.load_daily_returns("Russell 2000", trading_days_only=True)    # non-trading zeros dropped

mf.trailing_return("sp500", "YTD")   # windows: 1M,3M,6M,YTD,1Y,2Y,3Y,5Y,10Y
mf.cumulative_return("EM", "2025-12-31", "2026-06-30")
mf.latest_date(); mf.date_range(); mf.as_of_freshness()
```

Names are resolved flexibly: canonical name, a friendly **alias** (`sp500`, `agg`, `hy`,
`xbi`, `r2000`, `acwi ex us`, `eafe`, `em`, `t-bill`, …), or a raw Morningstar **SecId**.

Quick check:
```bash
python3 morningstar_feed.py     # prints freshness, coverage, and a few trailing returns
```

## On-disk contract (canonical feed — don't break for consumers)

| File | Columns |
|---|---|
| `benchmark_return_index_10yr.csv` | `Benchmark, Id, Date, Daily Return Index` |
| `benchmark_daily_ret_pct_10yr.csv` | `Benchmark, Id, Date, daily_ret_pct` |

The `_10yr` files are canonical; `benchmark_daily_return_index.csv` /
`benchmark_daily_returns_pct.csv` are the older 6-yr window, **superseded**. The TR index
base level is arbitrary — always use returns/accessors, never the raw level.

## Refresh (owner only)

Requires the `morningstar_data` SDK and a valid `MD_AUTH_TOKEN` (~24h TTL). Run the pull in
`GOVERNANCE.md` / `SKILL.md`, then **regenerate the manifest** so consumers see new coverage:

```bash
python3 build_manifest.py       # rewrites datasets.json (as_of, per-benchmark ranges, sha256)
```

Never commit tokens (`.env` is git-ignored).

## Also in this repo (point-in-time artifacts, not part of the programmatic feed)

- `completed_portfolio_2026-06-30.csv` — consolidated public-markets performance table
- `reconciliation_WR_2026-06-30.csv`, `reconciliation_WR_values_2026-06-30.csv` — WR reconciliation
