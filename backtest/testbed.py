"""Minimal local stand-in for the competition `testbed` module.

Only the two helpers the strategies import are provided. The observation built by
backtest/sim.py carries the completed daily closes under the private key `_daily`.
"""
import pandas as pd

SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'INTC', 'CRM', 'JPM', 'BAC', 'GS', 'V', 'PYPL', 'LLY', 'JNJ', 'UNH', 'PFE', 'TMO',
           'AMZN', 'TSLA', 'WMT', 'NKE', 'KO', 'CAT', 'GE', 'BA', 'XOM', 'CVX', 'GOOGL', 'META', 'DIS', 'T', 'NEE']


def get_daily_close(observation, lookback=253):
    d = observation["_daily"]
    return d.iloc[-lookback:] if isinstance(d, pd.DataFrame) else pd.DataFrame()


def zero_weights():
    return {s: 0.0 for s in SYMBOLS}
