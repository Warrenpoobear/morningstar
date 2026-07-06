"""Generate datasets.json — a machine-readable manifest of the benchmark feed.

Run after every refresh so downstream projects can discover coverage/freshness
programmatically:  python3 build_manifest.py
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import json
from pathlib import Path

import pandas as pd
import morningstar_feed as mf

HERE = Path(__file__).resolve().parent

FILES = [
    ("benchmark_return_index_10yr.csv", "Cumulative daily total-return index per benchmark (base arbitrary)",
     ["Benchmark", "Id", "Date", "Daily Return Index"]),
    ("benchmark_daily_ret_pct_10yr.csv", "Daily % returns = pct_change of the TR index (NaN first obs; 0 on non-trading days)",
     ["Benchmark", "Id", "Date", "daily_ret_pct"]),
    ("benchmark_daily_return_index.csv", "TR index, 6yr window (SUPERSEDED by _10yr)",
     ["Benchmark", "Id", "Date", "Daily Return Index"]),
    ("benchmark_daily_returns_pct.csv", "Daily % returns, 6yr window (SUPERSEDED by _10yr)",
     ["Benchmark", "Id", "Date", "daily_ret_pct"]),
]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    lo, hi = mf.date_range()
    cov = mf.list_benchmarks()
    files = []
    for name, desc, schema in FILES:
        p = HERE / name
        if not p.exists():
            continue
        n_rows = sum(1 for _ in open(p, encoding="utf-8")) - 1
        files.append({
            "file": name, "description": desc, "columns": schema,
            "rows": n_rows, "bytes": p.stat().st_size, "sha256": _sha(p),
        })

    manifest = {
        "feed": "wake-robin-morningstar-benchmarks",
        "version": "1.0.0",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "source": "Morningstar Direct (morningstar_data SDK)",
        "currency": "USD",
        "frequency": "daily",
        "as_of": hi.isoformat(),
        "coverage_start": lo.isoformat(),
        "n_benchmarks": len(mf.SEC_ID_MAP),
        "primary_files": {
            "return_index": mf.RETURN_INDEX_FILE,
            "daily_returns": mf.DAILY_RETURNS_FILE,
        },
        "accessor": {
            "module": "morningstar_feed",
            "env_override": "MORNINGSTAR_FEED_DIR",
            "key_functions": [
                "benchmark_names()", "list_benchmarks()", "resolve_name(name)", "secid(name)",
                "get_series(name, kind)", "load_return_index(names)", "load_daily_returns(names)",
                "trailing_return(name, window)", "cumulative_return(name, start, end)",
                "latest_date()", "as_of_freshness()",
            ],
        },
        "files": files,
        "benchmarks": [
            {"benchmark": r.benchmark, "secid": r.secid,
             "start": None if pd.isna(r.start) else str(r.start),
             "end": None if pd.isna(r.end) else str(r.end),
             "rows": int(r.rows)}
            for r in cov.itertuples()
        ],
        "notes": [
            "Return index base level is arbitrary; use pct_change / provided accessors for returns.",
            "Non-trading days repeat the prior index (daily_ret_pct = 0); load_daily_returns(trading_days_only=True) drops them.",
            "Newer indices (Russell/Roundhill Mag 7) have shorter history; pre-inception rows are absent.",
            "Not in the MD API: Bloomberg US Govt/Credit 1-5Yr, Bloomberg HY Muni, Credit Suisse HF, NCREIF, Galene, S&P UBS Leveraged Loan.",
        ],
        "refresh": "See GOVERNANCE.md / SKILL.md. Requires morningstar_data SDK + MD_AUTH_TOKEN (~24h TTL).",
    }
    out = HERE / "datasets.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {out}  ({len(files)} files, {len(manifest['benchmarks'])} benchmarks, as_of {hi})")


if __name__ == "__main__":
    main()
