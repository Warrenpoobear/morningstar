---
name: morningstar-benchmark
description: |
  Refresh or inspect Morningstar Direct benchmark daily return data. Use when the user says "refresh benchmark data", "update morningstar data", "pull benchmark returns", "how fresh is the benchmark data", "morningstar benchmark status", or similar. Repo: C:\Projects\morningstar. Pulls 29 benchmark TR series (Bloomberg, MSCI, Russell, S&P, FTSE Nareit, KBW, ETFs) via the morningstar_data Python SDK. Requires a valid MD_AUTH_TOKEN (~24h expiry).
allowed-tools:
  - Bash(python3 *)
  - Bash(ls *)
  - Bash(git *)
  - Bash(cp *)
  - Bash(cd *)
---

# Morningstar Benchmark Data

Refresh or inspect the 29-benchmark daily return dataset in `C:\Projects\morningstar`.

## Data location

```
/mnt/c/Projects/morningstar/
  benchmark_return_index_10yr.csv      # Cumulative TR index, 2016-07-01 → present
  benchmark_daily_ret_pct_10yr.csv     # Daily % returns (pct_change of TR index)
  GOVERNANCE.md                        # SecId map, limitations, refresh instructions
```

## SecId map (29 benchmarks)

```python
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
```

**Not in MD API:** Bloomberg US Govt/Credit 1-5 Yr, Bloomberg HY Muni, Credit Suisse HF, NCREIF, Galene, S&P UBS Leveraged Loan.

---

## Steps

### 1 — Check freshness

```bash
python3 - <<'EOF'
import os, sys, pandas as pd
from datetime import date

f = "/mnt/c/Projects/morningstar/benchmark_daily_ret_pct_10yr.csv"
if not os.path.exists(f):
    print(f"ERROR: data file not found at {f} — run Step 2 to do initial pull")
    sys.exit(1)

df = pd.read_csv(f, parse_dates=["Date"])
latest = df["Date"].max().date()
age = (date.today() - latest).days
n_benchmarks = df["Benchmark"].nunique()
n_rows = len(df)

status = "FRESH" if age <= 3 else f"STALE ({age}d behind)"
print(f"Latest date:   {latest}  [{status}]")
print(f"Benchmarks:    {n_benchmarks}")
print(f"Total rows:    {n_rows:,}")
print(f"Date range:    {df['Date'].min().date()} → {latest}")
EOF
```

If `FRESH` and the user only asked for a status check, stop here and report.

---

### 2 — Refresh (when stale or explicitly requested)

**Requires MD_AUTH_TOKEN.** `! export MD_AUTH_TOKEN=...` does NOT propagate to the Bash tool's subprocess — the token must be hardcoded directly into the script below. Ask the user to paste it in:

```
Get a fresh token from Morningstar Direct → Account → API Token
Then paste it as the TOKEN value in the script below.
```

```bash
python3 - <<'EOF'
import os, sys, pandas as pd
from datetime import date

# Paste token directly — env export does not propagate to subprocess
TOKEN = "<paste-token-here>"
if TOKEN == "<paste-token-here>" or not TOKEN:
    print("ERROR: TOKEN not set. Paste a fresh MD_AUTH_TOKEN into the script.")
    sys.exit(1)
os.environ["MD_AUTH_TOKEN"] = TOKEN

import morningstar_data as md
from morningstar_data.direct.data_type import Frequency

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
today = date.today().isoformat()

print(f"Pulling daily returns 2016-07-01 → {today}...")
try:
    df = md.direct.get_returns(
        investments=ids,
        start_date="2016-07-01",
        end_date=today,
        freq=Frequency.daily,
        currency="USD",
    )
except Exception as e:
    print(f"MD API error: {e}")
    sys.exit(1)

df["Benchmark"] = df["Id"].map(id_to_label)
df = df.sort_values(["Id", "Date"]).reset_index(drop=True)
df["daily_ret_pct"] = df.groupby("Id")["Daily Return Index"].pct_change(fill_method=None) * 100

SCRATCH = "/tmp/ms_refresh"
os.makedirs(SCRATCH, exist_ok=True)
df[["Benchmark","Id","Date","Daily Return Index"]].to_csv(f"{SCRATCH}/benchmark_return_index_10yr.csv", index=False)
df[["Benchmark","Id","Date","daily_ret_pct"]].to_csv(f"{SCRATCH}/benchmark_daily_ret_pct_10yr.csv", index=False)

print(f"Shape: {df.shape}  |  Latest: {df['Date'].max().date()}")
print(f"Written to {SCRATCH}/")
EOF
```

---

### 3 — Copy to repo and commit

```bash
REPO="/mnt/c/Projects/morningstar"
SCRATCH="/tmp/ms_refresh"

cp "$SCRATCH/benchmark_return_index_10yr.csv"   "$REPO/benchmark_return_index_10yr.csv"
cp "$SCRATCH/benchmark_daily_ret_pct_10yr.csv"  "$REPO/benchmark_daily_ret_pct_10yr.csv"

cd "$REPO"
git add benchmark_return_index_10yr.csv benchmark_daily_ret_pct_10yr.csv
git commit -m "Refresh benchmark data through $(date +%Y-%m-%d)"
git push
```

If `cp` fails with `Permission denied`, the files are open in Windows (Excel). Close them first, then retry. Alternatively write to new filenames and rename after closing.

---

## Report format

```
MORNINGSTAR BENCHMARK DATA — YYYY-MM-DD

Status:     FRESH / STALE (Nd behind)
Latest:     YYYY-MM-DD
Benchmarks: 29
Rows:       ~105,900 (10yr window)

[If refreshed]
  Pulled:    YYYY-MM-DD HH:MM
  Committed: <git sha>
  Pushed:    github.com/Warrenpoobear/morningstar

[If token needed]
  MD_AUTH_TOKEN expired or not set.
  Get a fresh token: Morningstar Direct → Account → API Token
  Paste into TOKEN = "..." in Step 2 script.

STATUS: FRESH ✓ / ⚠️ STALE (Nd) — refresh needed / 🚨 TOKEN_EXPIRED — get new MD_AUTH_TOKEN
```

## Notes

- **Token TTL:** ~24h. Token in conversation history should not be re-used across sessions — always source fresh.
- **Token propagation:** `! export MD_AUTH_TOKEN=...` does not reach the Bash tool subprocess. Always hardcode into the script via `os.environ["MD_AUTH_TOKEN"] = TOKEN`.
- **Weekend/holiday rows:** `daily_ret_pct = 0` (index repeats). Filter with a trading-day calendar before use.
- **Newer indices:** Russell Magnificent 7 and Roundhill MAGS ETF have shorter history; expect NaN before inception.
- **Remote:** `github.com/Warrenpoobear/morningstar` (private)

## Session-end learning

After completing this skill's task, if you encountered an unexpected behavior, constraint, API response, or workflow edge case, log it:

```
[LRN-YYYYMMDD-NNN]
Pattern-Key: SKILL_MORNINGSTAR_BENCHMARK_{description}
Area: hermes_ops | data_pipeline | research | portfolio
Promotion-lane: skill | none
Recurrence-Count: 1
Context: <one line — what happened>
Rule: <one line — what to do differently>
Suggested-Action: <patch to this SKILL.md, or none>
```

Recurrence ≥ 3 in 7 days → propose a patch to this `SKILL.md`. Full protocol: see `self-improving` skill.
