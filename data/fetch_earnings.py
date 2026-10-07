"""Earnings report days for the 30 names -> data/earnings_days.csv (symbol, gap_day, source).

`gap_day` = first trading day whose OPEN reflects the report (report before 09:30 ET -> that day, else next day).
Yahoo's quoteSummary API gives the exact report timestamps of the last 4 quarters and the next scheduled date; the
earnings-dates web page (older history) is not reachable from every network.  Older quarters are reconstructed:
anchor = a known report date shifted back by whole years, and the gap day is the day with the largest absolute
overnight gap (open / previous close) within +-8 trading days of the anchor. Known misses (MISS_TABLE) are exact.

    python3 data/fetch_earnings.py
"""
import os, sys
import numpy as np
import pandas as pd
from yfinance.data import YfData

HERE = os.path.dirname(os.path.abspath(__file__))
S = ['AAPL', 'MSFT', 'NVDA', 'INTC', 'CRM', 'JPM', 'BAC', 'GS', 'V', 'PYPL', 'LLY', 'JNJ', 'UNH', 'PFE', 'TMO',
     'AMZN', 'TSLA', 'WMT', 'NKE', 'KO', 'CAT', 'GE', 'BA', 'XOM', 'CVX', 'GOOGL', 'META', 'DIS', 'T', 'NEE']
O = pd.read_csv(os.path.join(HERE, "daily_open.csv"), index_col=0, parse_dates=True)
C = pd.read_csv(os.path.join(HERE, "daily_close.csv"), index_col=0, parse_dates=True)
GAP = (O / C.shift(1) - 1).abs()
DAYS = C.index


def gap_day(ts):
    ts = pd.Timestamp(ts)
    d = ts.normalize()
    if ts.hour * 60 + ts.minute >= 9 * 60 + 30:
        d = d + pd.Timedelta(days=1)
    i = DAYS.searchsorted(d)
    return DAYS[i] if i < len(DAYS) else d


def main():
    yd = YfData()
    rows = []
    for t in S:
        r = yd.get_raw_json(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{t}",
                            params={"modules": "earnings"})["quoteSummary"]["result"][0]["earnings"]
        known = [pd.Timestamp(q["reportedDate"]["raw"], unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None)
                 for q in r["earningsChart"]["quarterly"] if q.get("reportedDate")]
        nxt = [pd.Timestamp(x["raw"], unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None)
               for x in r["earningsChart"].get("earningsDate", [])]
        exact = set()
        for k in known:
            g = gap_day(k)
            exact.add(g)
            rows.append((t, g.date(), "yahoo"))
        for n in nxt:
            rows.append((t, gap_day(n).date(), "yahoo_next"))
        for k in known:
            for y in range(1, 8):
                a = pd.Timestamp(k) - pd.DateOffset(years=y)
                i = DAYS.searchsorted(a.normalize())
                if i <= 8 or i >= len(DAYS) - 8:
                    continue
                win = GAP[t].iloc[i - 8:i + 9]
                rows.append((t, win.idxmax().date(), "reconstructed"))
        print(t, len(known), nxt, flush=True)
    df = pd.DataFrame(rows, columns=["symbol", "gap_day", "source"]).drop_duplicates(["symbol", "gap_day"])
    df.sort_values(["symbol", "gap_day"]).to_csv(os.path.join(HERE, "earnings_days.csv"), index=False)
    print(df.groupby("source").size())


if __name__ == "__main__":
    main()
