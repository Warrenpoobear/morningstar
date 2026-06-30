# Morningstar Direct — Benchmark Data Governance

**Owner:** Wake Robin Capital Management  
**Last updated:** 2026-06-30  
**Data source:** Morningstar Direct API (`morningstar_data` Python SDK)

---

## Purpose

This folder holds daily benchmark total-return data pulled from Morningstar Direct for use in asset-class performance reporting, portfolio attribution, and risk analysis.

---

## Files

| File | Description | Rows | Date Range |
|---|---|---|---|
| `benchmark_return_index_10yr.csv` | Cumulative daily TR index per benchmark | ~105,908 | 2016-07-01 → 2026-06-30 |
| `benchmark_daily_ret_pct_10yr.csv` | Daily % returns (pct_change of TR index) | ~105,908 | 2016-07-01 → 2026-06-30 |
| `benchmark_daily_return_index.csv` | TR index, 6yr window (superseded) | ~68,817 | 2020-01-01 → 2026-06-30 |
| `benchmark_daily_returns_pct.csv` | Daily % returns, 6yr window (superseded) | ~68,817 | 2020-01-01 → 2026-06-30 |

### Column schema

**Return index files:**
```
Benchmark, Id, Date, Daily Return Index
```

**Daily % return files:**
```
Benchmark, Id, Date, daily_ret_pct
```

- `Benchmark` — human-readable label (matches the source dashboard names below)
- `Id` — Morningstar SecId used for the API call
- `Daily Return Index` — cumulative total return index (not a price; base level is arbitrary)
- `daily_ret_pct` — `(index_t / index_{t-1} - 1) * 100`; NaN on first observation per series

**Note:** Weekends and holidays carry forward the prior day's index value, producing `daily_ret_pct = 0`. Filter these out using a trading-day calendar if needed.

---

## Benchmark Coverage & SecId Map

| Dashboard Name | Morningstar SecId | Universe |
|---|---|---|
| Bloomberg Commodity TR USD | XIUSA04GUL | XI |
| Bloomberg Global Agg Hdg USD | FOUSA06K3V | XI |
| Bloomberg Global Agg USD | XIUSA000CU | XI |
| Bloomberg US Agg Bond TR USD | FOUSA05Y32 | XI |
| Bloomberg US Corp HY TR USD | XIUSA000C3 | XI |
| Bloomberg US Leveraged Loan Insur TR USD | F00001QI62 | XI |
| FTSE Nareit Composite TR | FOUSA06QVA | XI |
| FTSE Nareit Eqty Apartments TR | FOUSA06QUF | XI |
| KBW Nasdaq Bank TR USD | FOUSA06WRY | XI |
| MSCI ACWI Ex USA NR USD | XIUSA04G85 | XI |
| MSCI ACWI NR USD | XIUSA04EXL | XI |
| MSCI EAFE NR USD | XIUSA000PK | XI |
| MSCI EM NR USD | F00001DR59 | XI |
| Roundhill Magnificent Seven ETF | F00001EQOY | FE |
| Russell 1000 Growth TR USD | XIUSA000KO | XI |
| Russell 1000 TR USD | XIUSA000O4 | XI |
| Russell 1000 Value TR USD | XIUSA000KP | XI |
| Russell 2000 Growth TR USD | XIUSA000KQ | XI |
| Russell 2000 TR USD | XIUSA000O5 | XI |
| Russell 2000 Value TR USD | XIUSA000KR | XI |
| Russell 2500 TR USD | XIUSA000KZ | XI |
| Russell 2500 Value TR USD | XIUSA000L1 | XI |
| Russell 3000 Growth TR USD | XIUSA000KS | XI |
| Russell 3000 TR USD | XIUSA000O6 | XI |
| Russell 3000 Value TR USD | XIUSA000KT | XI |
| Russell Magnificent 7 TR USD | F00001T2BO | XI |
| S&P 500 TR USD | F00000W7S7 | XI |
| State Street SPDR S&P Biotech ETF | FEUSA04AER | FE |
| State Street SPDR Blmbg 1-3Mth T-Bill ETF | FOUSA06B85 | FE |

### Not available in Morningstar Direct API

The following benchmarks from the source dashboard could not be retrieved — no USD results returned under any search term:

| Dashboard Name | Reason |
|---|---|
| Bloomberg US Govt/Credit 1-5 Yr TR USD | Not found in MD API |
| Bloomberg HY Muni TR USD | Not found in MD API |
| Credit Suisse Hedge Fund USD | Discontinued post-UBS acquisition |
| NCREIF Property / Apartment | Private real estate data; not in MD |
| Galene Credit Fund [Proxy Returns] | Private fund; not in MD |
| S&P UBS Leveraged Loan USD | Not found in MD API |

---

## Refresh Instructions

**Requirements:**
- `morningstar_data` Python package installed (`pip install morningstar_data`)
- Valid `MD_AUTH_TOKEN` (JWT from Morningstar Direct → Account → API Token)
  - Tokens expire after ~24 hours

**To refresh:**

```python
import os
import morningstar_data as md
from morningstar_data.direct.data_type import Frequency
import pandas as pd

os.environ["MD_AUTH_TOKEN"] = "<your-token>"

SEC_ID_MAP = {
    "Bloomberg Commodity TR USD":                "XIUSA04GUL",
    "Bloomberg Global Agg Hdg USD":              "FOUSA06K3V",
    "Bloomberg Global Agg USD":                  "XIUSA000CU",
    "Bloomberg US Agg Bond TR USD":              "FOUSA05Y32",
    "Bloomberg US Corp HY TR USD":               "XIUSA000C3",
    "Bloomberg US Leveraged Loan Insur TR USD":  "F00001QI62",
    "FTSE Nareit Composite TR":                  "FOUSA06QVA",
    "FTSE Nareit Eqty Apartments TR":            "FOUSA06QUF",
    "KBW Nasdaq Bank TR USD":                    "FOUSA06WRY",
    "MSCI ACWI Ex USA NR USD":                   "XIUSA04G85",
    "MSCI ACWI NR USD":                          "XIUSA04EXL",
    "MSCI EAFE NR USD":                          "XIUSA000PK",
    "MSCI EM NR USD":                            "F00001DR59",
    "Roundhill Magnificent Seven ETF":           "F00001EQOY",
    "Russell 1000 Growth TR USD":                "XIUSA000KO",
    "Russell 1000 TR USD":                       "XIUSA000O4",
    "Russell 1000 Value TR USD":                 "XIUSA000KP",
    "Russell 2000 Growth TR USD":                "XIUSA000KQ",
    "Russell 2000 TR USD":                       "XIUSA000O5",
    "Russell 2000 Value TR USD":                 "XIUSA000KR",
    "Russell 2500 TR USD":                       "XIUSA000KZ",
    "Russell 2500 Value TR USD":                 "XIUSA000L1",
    "Russell 3000 Growth TR USD":                "XIUSA000KS",
    "Russell 3000 TR USD":                       "XIUSA000O6",
    "Russell 3000 Value TR USD":                 "XIUSA000KT",
    "Russell Magnificent 7 TR USD":              "F00001T2BO",
    "S&P 500 TR USD":                            "F00000W7S7",
    "State Street SPDR S&P Biotech ETF":         "FEUSA04AER",
    "State Street SPDR Blmbg 1-3Mth T-Bill ETF":"FOUSA06B85",
}

ids = list(SEC_ID_MAP.values())
id_to_label = {v: k for k, v in SEC_ID_MAP.items()}

df = md.direct.get_returns(
    investments=ids,
    start_date="2016-07-01",
    end_date="2026-06-30",   # update end_date each refresh
    freq=Frequency.daily,
    currency="USD",
)

df["Benchmark"] = df["Id"].map(id_to_label)
df = df.sort_values(["Id", "Date"]).reset_index(drop=True)
df["daily_ret_pct"] = df.groupby("Id")["Daily Return Index"].pct_change(fill_method=None) * 100

df[["Benchmark","Id","Date","Daily Return Index"]].to_csv("benchmark_return_index_10yr.csv", index=False)
df[["Benchmark","Id","Date","daily_ret_pct"]].to_csv("benchmark_daily_ret_pct_10yr.csv", index=False)
```

---

## Auth Token Notes

- Token is a short-lived JWT (~24h) issued by Morningstar Direct
- Set via `os.environ["MD_AUTH_TOKEN"]` or `export MD_AUTH_TOKEN="..."` in shell
- Do **not** commit tokens to this repository
- Source a fresh token from Morningstar Direct before each refresh session

---

## Limitations

- Daily return index values repeat on non-trading days (weekends, holidays), producing `daily_ret_pct = 0` — filter before use
- Some newer indices (Russell Magnificent 7, Roundhill MAGS ETF) have shorter history; pre-inception rows will be NaN
- The return index base level is arbitrary (not normalized to 100); use pct_change for all return calculations
- Monthly data in the source dashboard may differ slightly from values computed by chaining these daily returns due to rounding
