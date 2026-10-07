"""Download the price files used by backtest/ (Yahoo Finance via yfinance; needs network access).

    python3 data/fetch.py
"""
import os
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
S = ['AAPL', 'MSFT', 'NVDA', 'INTC', 'CRM', 'JPM', 'BAC', 'GS', 'V', 'PYPL', 'LLY', 'JNJ', 'UNH', 'PFE', 'TMO',
     'AMZN', 'TSLA', 'WMT', 'NKE', 'KO', 'CAT', 'GE', 'BA', 'XOM', 'CVX', 'GOOGL', 'META', 'DIS', 'T', 'NEE']

d = yf.download(S, start="2019-01-01", end="2026-01-01", auto_adjust=True, progress=False)
for f in ["Open", "High", "Low", "Close"]:
    d[f][S].to_csv(os.path.join(HERE, f"daily_{f.lower()}.csv"))
h = yf.download(S, period="730d", interval="60m", auto_adjust=True, progress=False)   # Yahoo keeps ~2 years of hourly bars
for f in ["Open", "Close"]:
    h[f][S].to_csv(os.path.join(HERE, f"hourly_{f.lower()}.csv"))
print("daily", d["Close"].shape, "hourly", h["Close"].shape)
