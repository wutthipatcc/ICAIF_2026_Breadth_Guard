"""jimin_hybrid_better_weight - original as provided (kept for comparison; the trailing extra quote on the
strategy.name line was removed so it parses). See jimin_hybrid_fh_nvda.py for the Finance/Healthcare/NVDA version.
"""
import numpy as np
import pandas as pd
from testbed import get_daily_close, zero_weights


# ---------------- helpers copied from jimin_test_v4 (miss table, 12-1 score, shock test) ----------------
MISS_DAYS = 15          # trading days to stay out after a miss
MISS_THR = -0.5         # EPS surprise (%) below which it counts as a miss

MISS_TABLE = {
    "AAPL": "20230203:-3.8",
    "AMZN": "20190726:-6.5 20191025:-7.1 20200501:-18.0 20211029:-30.9 20220429:-191.6 20220729:-273.3 20230203:-81.7",
    "BA": "20190424:-1.0 20191023:-31.4 20200129:-97.6 20200429:-14.3 20200729:-89.6 20210127:-826.0 20210429:-41.0 20211027:-299.0 20220126:-4731.9 20220427:-995.8 20220727:-246.3 20221026:-7213.3 20230125:-961.3 20230426:-20.9 20231025:-25.0 20240731:-44.2 20241023:-19.7 20250128:-56.1 20251029:-214.4 20260728:-141.5",
    "BAC": "20200415:-33.4 20220718:-2.1 20240112:-45.6 20240416:-1.8",
    "CAT": "20190128:-14.7 20190724:-9.4 20191023:-8.1 20200428:-4.5 20230131:-4.2 20241030:-3.4 20250430:-2.2 20250805:-3.7",
    "CRM": "20241204:-1.5",
    "CVX": "20190802:-2.8 20200731:-73.2 20210129:-111.4 20210430:-4.6 20220128:-18.0 20220429:-2.7 20230127:-4.8 20231027:-17.1 20240802:-14.9 20250131:-2.3",
    "DIS": "20190807:-22.4 20200506:-33.0 20211111:-23.4 20220512:-9.2 20221109:-46.9 20230511:-0.9",
    "GE": "20190131:-24.1 20200429:-38.0 20200729:-66.4 20210126:-6.3 20221025:-28.1",
    "GOOGL": "20190430:-5.0 20191029:-18.8 20200429:-3.4 20220427:-4.4 20220727:-5.0 20221026:-15.3 20230203:-11.9",
    "GS": "20191015:-1.8 20200115:-14.0 20200415:-7.4 20220118:-9.4 20230117:-42.4 20230719:-19.6 20231017:-1.0",
    "INTC": "20220729:-58.3 20230127:-50.5 20240802:-80.2 20241101:-1533.5 20250725:-1169.5",
    "JPM": "20190115:-9.5 20200714:-10.4 20220413:-2.9 20220714:-4.8 20240112:-15.7 20260113:-3.9",
    "LLY": "20201027:-10.0 20210427:-10.9 20210803:-1.0 20211026:-1.2 20220203:-0.7 20220804:-26.3 20230427:-6.3 20241030:-19.5 20250501:-3.4",
    "META": "20190425:-47.3 20190725:-50.8 20220203:-4.1 20220728:-3.4 20221027:-12.1 20230202:-21.5 20251030:-84.3 20260730:-14.4",
    "MSFT": "20220727:-2.7",
    "NEE": "20190125:-3.0 20200124:-2.5",
    "NKE": "20190628:-5.4 20200325:-2.7 20200626:-858.5 20230630:-2.3",
    "NVDA": "20220825:-1.5 20221117:-17.3",
    "PFE": "20200128:-4.5 20210202:-9.7",
    "PYPL": "20200507:-11.6 20220202:-1.0 20240430:-11.4 20260203:-4.4",
    "T": "20200422:-1.4 20240124:-3.2 20240724:-0.6 20250423:-0.9",
    "TMO": "20230726:-5.2",
    "TSLA": "20190131:-6.5 20190425:-209.6 20190725:-182.3 20210128:-23.9 20231019:-9.8 20240125:-3.5 20240424:-8.1 20240724:-16.1 20250130:-5.1 20250423:-34.9 20250724:-1.1 20251023:-10.5 20260723:-39.1",
    "UNH": "20250417:-1.3 20250729:-8.2",
    "WMT": "20200218:-3.8 20210218:-8.0 20220517:-12.1 20250821:-8.0",
    "XOM": "20190426:-24.5 20190802:-13.6 20200131:-9.6 20200731:-17.1 20220429:-7.0 20230728:-3.9 20231027:-3.8 20240426:-4.8",
}


def _parse_table():
    out = {}
    for t, s in MISS_TABLE.items():
        out[t] = sorted((pd.Timestamp(x.split(":")[0]), float(x.split(":")[1])) for x in s.split() if x)
    return out


_MISS = _parse_table()


def add_miss(ticker, yyyymmdd, surprise):
    """Register a new miss at runtime (effective day = first Round-1 day on which the report is public)."""
    _MISS.setdefault(ticker, []).append((pd.Timestamp(yyyymmdd), float(surprise)))
    _MISS[ticker].sort()


def _zscore(x):
    x = np.asarray(x, dtype=float)
    m, s = np.nanmean(x), np.nanstd(x)
    z = (x - m) / s if s > 0 else np.zeros_like(x)
    return np.clip(np.nan_to_num(z), -2.5, 2.5)


def _decision_day(observation, daily):
    """Calendar date of the current Round-1 decision. Prefer an explicit date in the observation; otherwise the next
    business day after the last completed daily close."""
    rnd = observation.get("round", {}) or {}
    for key in ("day", "date", "trading_day", "as_of", "deadline", "execution_time", "id"):
        v = rnd.get(key) if isinstance(rnd, dict) else None
        if v:
            try:
                s = str(v)
                if key == "id":
                    s = s.split("-r")[0].split("-", 1)[1]        # validation-YYYY-MM-DD-r1
                return pd.Timestamp(s[:10])
            except Exception:
                pass
    for key in ("as_of", "timestamp", "date", "day"):
        v = observation.get(key)
        if v:
            try:
                return pd.Timestamp(str(v)[:10])
            except Exception:
                pass
    last = pd.Timestamp(daily.index[-1]).normalize()
    return last + pd.offsets.BDay(1)


def _excluded(observation, daily, syms):
    """Boolean mask: stocks with a miss whose effective day is within the last MISS_DAYS trading days (inclusive of today)."""
    today = _decision_day(observation, daily)
    idx = pd.DatetimeIndex(daily.index).normalize()
    past = idx[idx < today]
    start = past[-(MISS_DAYS - 1)] if len(past) >= MISS_DAYS - 1 else (past[0] if len(past) else today)
    out = np.zeros(len(syms), dtype=bool)
    for j, t in enumerate(syms):
        for d, s in _MISS.get(t, []):
            if s < MISS_THR and start <= d <= today:
                out[j] = True
                break
    return out


SHOCK_DROP = -0.02        # previous-day equal-weight return (close-to-close) that counts as a shock


def _signal_121(daily, n):
    if len(daily) < 253:
        return np.zeros(n)
    raw = daily.iloc[-22].values / daily.iloc[-253].values - 1   # return from t-252 to t-21
    return _zscore(raw)


def _shock_yesterday(daily):
    """True if the equal-weight average of the stocks fell by SHOCK_DROP or more from the close two days ago to the
    last close (the last completed trading day before this Round 1)."""
    if len(daily) < 2:
        return False
    r = daily.iloc[-1].values / daily.iloc[-2].values - 1
    r = r[np.isfinite(r)]
    return bool(len(r)) and float(np.mean(r)) <= SHOCK_DROP




# ---------------- v5 ----------------
NAME = "jimin_hybrid_better_weight"
LOOKBACK = 400
BETA_WIN = 120
SHOCK_LAST_DAY = 10                                  # raise S only if today's window day index <= 10
PHASE_START = {"validation": ("2026-10-08", "2026-10-09"), "official": ("2026-10-12", "2026-10-30")}
_START = {}                                          # fallback cache: window start = first decision day with an empty book
SECTOR = {'GOOGL': 'Comm', 'META': 'Comm', 'NEE': 'Comm', 'T': 'Comm', 'DIS': 'Comm',
          'WMT': 'Cons', 'KO': 'Cons', 'TSLA': 'Cons', 'AMZN': 'Cons', 'NKE': 'Cons',
          'BAC': 'Fin', 'GS': 'Fin', 'PYPL': 'Fin', 'JPM': 'Fin', 'V': 'Fin',
          'UNH': 'Hlth', 'JNJ': 'Hlth', 'LLY': 'Hlth', 'PFE': 'Hlth', 'TMO': 'Hlth',
          'XOM': 'Ind', 'GE': 'Ind', 'CVX': 'Ind', 'CAT': 'Ind', 'BA': 'Ind',
          'MSFT': 'Tech', 'INTC': 'Tech', 'CRM': 'Tech', 'NVDA': 'Tech', 'AAPL': 'Tech'}


def residual_momentum(daily, L=BETA_WIN):
    """daily: DataFrame of closes (rows = days, oldest first). Returns raw residual-momentum score per column (NaN if short)."""
    X = daily.values.astype(float)
    n = X.shape[1]
    if len(X) < 252 + L + 1:
        return None
    R = np.log(X[1:] / X[:-1])                       # R[j] = return into day j+1
    R = np.where(np.isfinite(R), R, np.nan)
    ok = np.isfinite(R)
    Rz = np.where(ok, R, 0.0)
    mkt = Rz.sum(1) / np.maximum(ok.sum(1), 1)
    sec = np.array([SECTOR.get(c, c) for c in daily.columns])
    M = (sec[:, None] == sec[None, :]).astype(float)
    cnt = ok.astype(float) @ M
    sec_ex = np.where(cnt - ok > 0, (Rz @ M - Rz) / np.maximum(cnt - ok, 1), mkt[:, None])
    T = len(R)
    x1 = np.repeat(mkt[:, None], n, 1); x2 = sec_ex

    def ws(Z):                                        # sum over [t-L, t) for each t
        cs = np.cumsum(np.vstack([np.zeros((1, n)), Z]), 0)
        out = np.full((T, n), np.nan)
        out[L:] = cs[L:T] - cs[:T - L]
        return out
    S11, S12, S22, S1y, S2y = ws(x1 * x1), ws(x1 * x2), ws(x2 * x2), ws(x1 * Rz), ws(x2 * Rz)
    det = S11 * S22 - S12 ** 2
    with np.errstate(all="ignore"):
        b1 = (S22 * S1y - S12 * S2y) / det
        b2 = (S11 * S2y - S12 * S1y) / det
    E = R - b1 * x1 - b2 * x2
    # last row of R = return into the last completed day (t-1). formation days t-252 .. t-22  -> R rows [-252, -21)
    e = E[-252:-21]
    with np.errstate(all="ignore"):
        s = np.nansum(e, 0) / (np.nanstd(e, 0) + 1e-12)
    s[np.isnan(e).any(0)] = np.nan
    return s


def _signal(daily, n):
    s = residual_momentum(daily)
    if s is None:
        return _signal_121(daily, n)                  # not enough history -> v4's 12-1 momentum
    return _zscore(s)




# ---------------- pair 방식 sleeve (exposure) ----------------
REGIME_POLICIES = {
    "rising":   {"base": 2.627288446515642e-05, "shock_add": 0.013954317839652966},
    "sideways": {"base": 0.00011271559722628338, "shock_add": 0.00963481382287418},
    "falling":  {"base": 0.000324794909938672,  "shock_add": 0.029324521428658722},
}
SLEEVE_SCALE = 0.5         # pair V5.1 비중의 절반 (pair보다 MDD·TO 순위가 한 칸 앞서도록)
WEAK_MARKET = -0.025       # 20일 시장수익률이 이보다 낮으면 비중 x WEAK_MULT
WEAK_MULT = 0.70
TILT_FRAC = 0.01           # theta = TILT_FRAC * E  (균등 E/30 대비 기울기)
BAND_FRAC = 1.00           # 무매매 밴드 = BAND_FRAC * E (한 번 사면 사실상 그대로 보유)
STEP = 0.5                 # 절반 스텝
PER_NAME_CAP = 0.30

_boost = {"on": False}     # 충격 이후 비중 상향 상태 (창이 바뀌면 첫 결정에서 초기화)



def regime_from_daily(daily):
    """완료된 종가만 사용: 60일 추세 + 20일 확인 + 경로 효율."""
    if len(daily) < 61:
        return "sideways"
    r = daily.pct_change(fill_method=None).iloc[-60:].mean(axis=1).to_numpy()
    if not np.isfinite(r).all():
        return "sideways"
    cumulative = float(np.prod(1 + r) - 1)
    recent = float(np.prod(1 + r[-20:]) - 1)
    efficiency = abs(float(r.sum())) / max(float(np.abs(r).sum()), 1e-12)
    if cumulative > 0.04 and recent > 0 and efficiency > 0.15:
        return "rising"
    if cumulative < -0.04 and recent < 0 and efficiency > 0.15:
        return "falling"
    return "sideways"


def _exposure(daily, cur_sum, started):
    policy = REGIME_POLICIES[regime_from_daily(daily)]
    base = policy["base"] * SLEEVE_SCALE
    boosted = min(1.0, base + policy["shock_add"] * SLEEVE_SCALE)
    if not started:
        _boost["on"] = False                                    # 새 창의 첫 결정
    elif cur_sum > (base + boosted) / 2:
        _boost["on"] = True                                     # 이미 상향된 책 (상태 복원)
    if started and _shock_yesterday(daily):
        _boost["on"] = True
    E = boosted if _boost["on"] else base
    if len(daily) >= 21:
        market20 = float((daily.iloc[-1] / daily.iloc[-21] - 1).mean())
        if np.isfinite(market20) and market20 < WEAK_MARKET:
            E *= WEAK_MULT
    return float(min(1.0, max(E, 0.0)))


LOOKBACK = 400             # residual momentum: 252 + 120 + 1 완료 종가 필요, 부족하면 12-1 momentum
BUY_BANNED = frozenset({"INTC", "CRM", "TSLA"})


def strategy(observation):
    syms = observation["symbols"]
    n = len(syms)
    port = observation["portfolio"]
    started = bool(port.get("positions"))
    w = port.get("weights") or {}
    positions = port.get("positions") or {}
    has_banned = any(float(w.get(s, 0.0)) > 0 or bool(positions.get(s)) for s in BUY_BANNED)
    if started and observation["round"]["number"] != 1 and not has_banned:
        return None                                             # 하루 한 번, Round 1에만 판단
    daily = get_daily_close(observation, lookback=LOOKBACK).reindex(columns=syms)
    cur = np.array([float(w.get(s, 0.0)) for s in syms])
    fired_before = _boost["on"]
    E = _exposure(daily, float(cur.sum()), started)
    fire = started and _boost["on"] and not fired_before        # 이번 결정에서 충격이 처음 걸림

    z = _signal(daily, n)
    target = np.clip(E / n + TILT_FRAC * E * z, 0.0, PER_NAME_CAP)
    if target.sum() > 0:
        target = target * (E / target.sum())
    # Never hold banned stocks; allocate their intended weights to NVDA.
    banned = np.array([s in BUY_BANNED for s in syms], dtype=bool)
    nvda_idx = syms.index("NVDA") if "NVDA" in syms else None
    if nvda_idx is not None:
        target[nvda_idx] += target[banned].sum()
    target[banned] = 0.0
    excl = _excluded(observation, daily, syms)
    excl |= banned
    target[excl] = 0.0

    if not started or fire or has_banned:
        new = target                                            # 최초 매수 / 충격 직후 상향
    else:
        must_sell = bool((excl & (cur > 0)).any())
        if float(np.abs(target - cur).sum()) < BAND_FRAC * E and not must_sell:
            return None                                         # 밴드 안: 제출하지 않음 (수수료 0, 거래 0)
        new = cur + STEP * (target - cur)
        new[excl] = 0.0
    new = np.clip(new, 0.0, PER_NAME_CAP)
    if new.sum() > 1:
        new = new / new.sum()
    out = zero_weights()
    out.update({s: float(v) for s, v in zip(syms, new)})
    out.update({s: 0.0 for s in BUY_BANNED})
    return out


strategy.name = "jimin_hybrid_better_weight"
