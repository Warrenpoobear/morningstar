"""morningstar_feed — read-only accessor for the Wake Robin Morningstar benchmark data feed.

Other projects consume the 29-benchmark daily total-return series through this module
rather than reading the CSVs by hand. It is dependency-light (pandas only) and resolves
its data directory relative to this file, so it works regardless of the caller's CWD.

Quickstart
----------
    import morningstar_feed as mf

    mf.benchmark_names()                       # -> ['Bloomberg Commodity TR USD', ...]
    mf.latest_date()                           # -> datetime.date(2026, 6, 30)
    mf.get_series("S&P 500")                    # -> pd.Series (return index), aliases OK
    mf.trailing_return("sp500", window="1Y")   # -> 22.32  (percent; annualized >1Y)
    mf.load_daily_returns(["S&P 500","US Agg"]) # -> wide DataFrame, trading days only

Point another checkout at a different copy of the data with the MORNINGSTAR_FEED_DIR env var.

Data contract (canonical on-disk feed, do not break for consumers):
    benchmark_return_index_10yr.csv   columns: Benchmark, Id, Date, Daily Return Index
    benchmark_daily_ret_pct_10yr.csv  columns: Benchmark, Id, Date, daily_ret_pct
See GOVERNANCE.md for provenance, the SecId map, refresh steps, and limitations.
"""
from __future__ import annotations

import datetime as _dt
import functools
import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

__all__ = [
    "DATA_DIR", "SEC_ID_MAP", "benchmark_names", "list_benchmarks", "resolve_name",
    "secid", "latest_date", "date_range", "load_return_index", "load_daily_returns",
    "get_series", "cumulative_return", "trailing_return", "as_of_freshness",
]

# --- data location (override with MORNINGSTAR_FEED_DIR) -----------------------
DATA_DIR = Path(os.environ.get("MORNINGSTAR_FEED_DIR", Path(__file__).resolve().parent))

RETURN_INDEX_FILE = "benchmark_return_index_10yr.csv"
DAILY_RETURNS_FILE = "benchmark_daily_ret_pct_10yr.csv"

# --- canonical benchmark -> Morningstar SecId (see GOVERNANCE.md) -------------
SEC_ID_MAP: dict[str, str] = {
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
    "State Street SPDR Blmbg 1-3Mth T-Bill ETF": "FOUSA06B85",
}

# --- friendly aliases -> canonical name (keys are normalized on lookup) -------
ALIASES: dict[str, str] = {
    "sp500": "S&P 500 TR USD", "s&p 500": "S&P 500 TR USD", "s&p500": "S&P 500 TR USD",
    "spx": "S&P 500 TR USD", "sp 500": "S&P 500 TR USD",
    "us agg": "Bloomberg US Agg Bond TR USD", "agg": "Bloomberg US Agg Bond TR USD",
    "us aggregate": "Bloomberg US Agg Bond TR USD", "bloomberg us agg": "Bloomberg US Agg Bond TR USD",
    "hy": "Bloomberg US Corp HY TR USD", "us hy": "Bloomberg US Corp HY TR USD",
    "high yield": "Bloomberg US Corp HY TR USD", "us corp hy": "Bloomberg US Corp HY TR USD",
    "commodities": "Bloomberg Commodity TR USD", "commodity": "Bloomberg Commodity TR USD",
    "bcom": "Bloomberg Commodity TR USD",
    "global agg": "Bloomberg Global Agg USD", "global agg hedged": "Bloomberg Global Agg Hdg USD",
    "leveraged loan": "Bloomberg US Leveraged Loan Insur TR USD",
    "lev loan": "Bloomberg US Leveraged Loan Insur TR USD",
    "bank loan": "Bloomberg US Leveraged Loan Insur TR USD",
    "nareit": "FTSE Nareit Composite TR", "reit": "FTSE Nareit Composite TR",
    "nareit composite": "FTSE Nareit Composite TR",
    "nareit apartments": "FTSE Nareit Eqty Apartments TR", "apartments": "FTSE Nareit Eqty Apartments TR",
    "kbw": "KBW Nasdaq Bank TR USD", "kbw bank": "KBW Nasdaq Bank TR USD",
    "banks": "KBW Nasdaq Bank TR USD", "bank index": "KBW Nasdaq Bank TR USD",
    "acwi ex us": "MSCI ACWI Ex USA NR USD", "acwi ex usa": "MSCI ACWI Ex USA NR USD",
    "acwi xus": "MSCI ACWI Ex USA NR USD", "acwi ex-us": "MSCI ACWI Ex USA NR USD",
    "acwi": "MSCI ACWI NR USD",
    "eafe": "MSCI EAFE NR USD", "developed ex us": "MSCI EAFE NR USD",
    "em": "MSCI EM NR USD", "emerging markets": "MSCI EM NR USD", "emerging": "MSCI EM NR USD",
    "roundhill mag7": "Roundhill Magnificent Seven ETF", "mags": "Roundhill Magnificent Seven ETF",
    "r1000g": "Russell 1000 Growth TR USD", "russell 1000 growth": "Russell 1000 Growth TR USD",
    "r1000": "Russell 1000 TR USD", "russell 1000": "Russell 1000 TR USD",
    "r1000v": "Russell 1000 Value TR USD", "russell 1000 value": "Russell 1000 Value TR USD",
    "r2000g": "Russell 2000 Growth TR USD", "russell 2000 growth": "Russell 2000 Growth TR USD",
    "r2000": "Russell 2000 TR USD", "russell 2000": "Russell 2000 TR USD",
    "r2000v": "Russell 2000 Value TR USD", "russell 2000 value": "Russell 2000 Value TR USD",
    "r2500": "Russell 2500 TR USD", "russell 2500": "Russell 2500 TR USD",
    "r2500v": "Russell 2500 Value TR USD", "russell 2500 value": "Russell 2500 Value TR USD",
    "r3000g": "Russell 3000 Growth TR USD", "russell 3000 growth": "Russell 3000 Growth TR USD",
    "r3000": "Russell 3000 TR USD", "russell 3000": "Russell 3000 TR USD",
    "r3000v": "Russell 3000 Value TR USD", "russell 3000 value": "Russell 3000 Value TR USD",
    "mag7": "Russell Magnificent 7 TR USD", "magnificent 7": "Russell Magnificent 7 TR USD",
    "magnificent seven": "Russell Magnificent 7 TR USD", "russell mag7": "Russell Magnificent 7 TR USD",
    "xbi": "State Street SPDR S&P Biotech ETF", "biotech": "State Street SPDR S&P Biotech ETF",
    "sp biotech": "State Street SPDR S&P Biotech ETF", "s&p biotech": "State Street SPDR S&P Biotech ETF",
    "t-bill": "State Street SPDR Blmbg 1-3Mth T-Bill ETF", "tbill": "State Street SPDR Blmbg 1-3Mth T-Bill ETF",
    "bil": "State Street SPDR Blmbg 1-3Mth T-Bill ETF", "1-3 mth t-bill": "State Street SPDR Blmbg 1-3Mth T-Bill ETF",
    "cash": "State Street SPDR Blmbg 1-3Mth T-Bill ETF",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


_NORM_CANON = {_norm(k): k for k in SEC_ID_MAP}


def resolve_name(name: str) -> str:
    """Map a benchmark name/alias/SecId to its canonical benchmark name."""
    if name in SEC_ID_MAP:
        return name
    if name in SEC_ID_MAP.values():  # a SecId
        return {v: k for k, v in SEC_ID_MAP.items()}[name]
    n = _norm(name)
    if n in _NORM_CANON:
        return _NORM_CANON[n]
    if n in ALIASES:
        return ALIASES[n]
    # fuzzy hint
    hits = [k for k in SEC_ID_MAP if n in _norm(k)]
    hint = f" Did you mean: {hits[:5]}?" if hits else ""
    raise KeyError(f"Unknown benchmark {name!r}.{hint} See morningstar_feed.benchmark_names().")


def secid(name: str) -> str:
    """Morningstar SecId for a benchmark name/alias."""
    return SEC_ID_MAP[resolve_name(name)]


def benchmark_names() -> list[str]:
    """Sorted list of the 29 canonical benchmark names."""
    return sorted(SEC_ID_MAP)


def list_benchmarks() -> pd.DataFrame:
    """DataFrame of canonical name + SecId + this feed's date coverage per benchmark."""
    idx = _load(RETURN_INDEX_FILE)
    cov = idx.groupby("Benchmark")["Date"].agg(["min", "max", "count"])
    rows = []
    for name, sid in sorted(SEC_ID_MAP.items()):
        c = cov.loc[name] if name in cov.index else None
        rows.append({
            "benchmark": name, "secid": sid,
            "start": None if c is None else c["min"].date(),
            "end": None if c is None else c["max"].date(),
            "rows": 0 if c is None else int(c["count"]),
        })
    return pd.DataFrame(rows)


@functools.lru_cache(maxsize=4)
def _load(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Feed file not found: {path}. Set MORNINGSTAR_FEED_DIR to the checkout, "
            f"or run the refresh in SKILL.md/GOVERNANCE.md."
        )
    df = pd.read_csv(path, parse_dates=["Date"])
    return df


def _wide(filename: str, value_col: str, names, start, end) -> pd.DataFrame:
    df = _load(filename)
    if names is not None:
        canon = [resolve_name(n) for n in ([names] if isinstance(names, str) else names)]
        df = df[df["Benchmark"].isin(canon)]
    wide = df.pivot_table(index="Date", columns="Benchmark", values=value_col, aggfunc="last")
    if start is not None:
        wide = wide[wide.index >= pd.Timestamp(start)]
    if end is not None:
        wide = wide[wide.index <= pd.Timestamp(end)]
    return wide.sort_index()


def latest_date() -> _dt.date:
    """Most recent Date in the feed."""
    return _load(RETURN_INDEX_FILE)["Date"].max().date()


def date_range() -> tuple[_dt.date, _dt.date]:
    d = _load(RETURN_INDEX_FILE)["Date"]
    return d.min().date(), d.max().date()


def load_return_index(names: Iterable[str] | str | None = None,
                      start=None, end=None) -> pd.DataFrame:
    """Wide DataFrame (Date x benchmark) of the cumulative TR index (base is arbitrary)."""
    return _wide(RETURN_INDEX_FILE, "Daily Return Index", names, start, end)


def load_daily_returns(names: Iterable[str] | str | None = None,
                       start=None, end=None, trading_days_only: bool = True) -> pd.DataFrame:
    """Wide DataFrame (Date x benchmark) of daily % returns.

    trading_days_only drops carried-forward non-trading rows (all-zero across series),
    per GOVERNANCE.md.
    """
    wide = _wide(DAILY_RETURNS_FILE, "daily_ret_pct", names, start, end)
    if trading_days_only:
        wide = wide[~(wide.fillna(0) == 0).all(axis=1)]
    return wide


def get_series(name: str, kind: str = "return_index", start=None, end=None) -> pd.Series:
    """Single benchmark as a Series indexed by Date. kind in {'return_index','daily_return'}."""
    canon = resolve_name(name)
    if kind in ("return_index", "index", "return"):
        s = load_return_index(canon, start, end)[canon]
    elif kind in ("daily_return", "daily", "pct"):
        s = load_daily_returns(canon, start, end)[canon]
    else:
        raise ValueError("kind must be 'return_index' or 'daily_return'")
    s.name = canon
    return s.dropna()


def _index_at(idx: pd.Series, when) -> float:
    """TR-index value at/just-before a date (nearest prior trading day)."""
    sub = idx[idx.index <= pd.Timestamp(when)]
    if sub.empty:
        raise ValueError(f"No data on/before {when} for {idx.name!r} (starts {idx.index.min().date()}).")
    return float(sub.iloc[-1])


def cumulative_return(name: str, start, end=None) -> float:
    """Cumulative total return (%) between two dates, inclusive of nearest prior trading days."""
    idx = get_series(name, "return_index")
    end = end or idx.index.max()
    return (_index_at(idx, end) / _index_at(idx, start) - 1) * 100


def trailing_return(name: str, window: str = "1Y", as_of=None, annualize: str = "auto") -> float:
    """Trailing total return (%). window in {1M,3M,6M,YTD,1Y,2Y,3Y,5Y,10Y}.

    Multi-year windows are annualized when annualize='auto' (matches Morningstar convention);
    pass annualize='never' for cumulative.
    """
    idx = get_series(name, "return_index")
    end = pd.Timestamp(as_of) if as_of is not None else idx.index.max()
    w = window.upper().strip()
    years = {"1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5, "10Y": 10}
    if w == "YTD":
        start = pd.Timestamp(_dt.date(end.year - 1, 12, 31))
    elif w in ("1M", "3M", "6M"):
        start = end - pd.DateOffset(months=int(w[:-1]))
    elif w in years:
        start = end - pd.DateOffset(years=years[w])
    else:
        raise ValueError("window must be one of 1M,3M,6M,YTD,1Y,2Y,3Y,5Y,10Y")
    v_end, v_start = _index_at(idx, end), _index_at(idx, start)
    total = v_end / v_start
    n = years.get(w)
    if n and n > 1 and annualize == "auto":
        return (total ** (1 / n) - 1) * 100
    return (total - 1) * 100


def as_of_freshness(warn_days: int = 4) -> dict:
    """Freshness summary: latest date, age in days, FRESH/STALE flag."""
    latest = latest_date()
    age = (_dt.date.today() - latest).days
    return {"latest": latest, "age_days": age, "status": "FRESH" if age <= warn_days else "STALE",
            "n_benchmarks": len(SEC_ID_MAP)}


def main() -> None:  # smoke test / CLI summary
    print("Morningstar benchmark feed @", DATA_DIR)
    print("freshness:", as_of_freshness())
    lo, hi = date_range()
    print(f"coverage: {lo} -> {hi}  |  {len(SEC_ID_MAP)} benchmarks")
    for nm in ["S&P 500", "US Agg", "Russell 2000", "XBI"]:
        print(f"  {nm:14} 1M={trailing_return(nm,'1M'):6.2f}  YTD={trailing_return(nm,'YTD'):6.2f}"
              f"  1Y={trailing_return(nm,'1Y'):6.2f}  5Y={trailing_return(nm,'5Y'):6.2f}")


if __name__ == "__main__":
    main()
