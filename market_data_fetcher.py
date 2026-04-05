"""
market_data_fetcher.py
Pre-fetches market data via yfinance + financialdatasets.ai REST API.
Calculates technical indicators and fundamentals.
Returns a structured data block to inject into the Claude prompt.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import warnings
import os
import urllib.request
import json
warnings.filterwarnings("ignore")

def _load_api_key():
    key = os.environ.get("FINANCIAL_DATASETS_API_KEY", "")
    if key:
        return key
    # Fallback: read from Windows user environment via PowerShell (handles setx persistence)
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             "[System.Environment]::GetEnvironmentVariable('FINANCIAL_DATASETS_API_KEY', 'User')"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""

FINANCIAL_DATASETS_API_KEY = _load_api_key()

# Tickers to pull fundamentals for — major bellwethers across sectors
FUNDAMENTAL_TICKERS = [
    # Mega-cap tech / NDX proxies
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
    # Energy majors
    "XOM", "CVX",
    # Financials
    "JPM", "GS",
    # Macro / rates sensitive
    "BRK-B", "UNH",
]


# ── Asset Configuration ────────────────────────────────────────────────────────

CORE_ASSETS = {
    "SPX":       "^GSPC",
    "NDX":       "^NDX",
    "DXY":       "DX-Y.NYB",
    "Gold":      "GC=F",
    "Silver":    "SI=F",
    "WTI Crude": "CL=F",
    "10Y Yield": "^TNX",
    "VIX":       "^VIX",
    "BTC/USD":   "BTC-USD",
}

GLOBAL_INDICES = {
    "Nikkei 225": "^N225",
    "DAX":        "^GDAXI",
    "FTSE 100":   "^FTSE",
    "EM (EEM)":   "EEM",
    "Copper":     "HG=F",
    "Nat Gas":    "NG=F",
}

SECTORS = {
    "XLE (Energy)":       "XLE",
    "XLK (Tech)":         "XLK",
    "XLF (Financials)":   "XLF",
    "XLP (Staples)":      "XLP",
    "XLI (Industrials)":  "XLI",
    "XLV (Healthcare)":   "XLV",
    "XLU (Utilities)":    "XLU",
    "XLRE (Real Estate)": "XLRE",
}

FIXED_INCOME_FX = {
    "TLT (20Y Treasury)": "TLT",
    "HYG (High Yield)":   "HYG",
    "LQD (IG Credit)":    "LQD",
    "EUR/USD":            "EURUSD=X",
    "GBP/USD":            "GBPUSD=X",
    "USD/JPY":            "JPY=X",
}

CRYPTO_EXTENDED = {
    "ETH/USD": "ETH-USD",
    "SOL/USD": "SOL-USD",
}

# All unique tickers to download in one batch
_ALL_TICKERS = list(set(
    list(CORE_ASSETS.values()) +
    list(GLOBAL_INDICES.values()) +
    list(SECTORS.values()) +
    list(FIXED_INCOME_FX.values()) +
    list(CRYPTO_EXTENDED.values()) +
    ["SPY", "QQQ", "^VIX3M"]
))


# ── Technical Indicator Calculations ──────────────────────────────────────────

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return float((100 - 100 / (1 + rs)).iloc[-1])


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(hist.iloc[-1])


def calc_bollinger_pctb(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    upper = sma + std_dev * sigma
    lower = sma - std_dev * sigma
    pct_b = (series - lower) / (upper - lower)
    return float(pct_b.iloc[-1])


def calc_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return float(tr.ewm(com=period - 1, min_periods=period).mean().iloc[-1])


def macd_label(hist):
    if hist > 0:
        return "Bullish"
    else:
        return "Bearish"


def rsi_label(val):
    if val >= 70:
        return f"{val:.0f} [Overbought]"
    elif val <= 30:
        return f"{val:.0f} [Oversold]"
    else:
        return f"{val:.0f}"


def pctb_label(val):
    if val > 1.0:
        return f"{val:.2f} [Above BB]"
    elif val < 0.0:
        return f"{val:.2f} [Below BB]"
    elif val > 0.8:
        return f"{val:.2f} [Near upper]"
    elif val < 0.2:
        return f"{val:.2f} [Near lower]"
    else:
        return f"{val:.2f}"


# ── Data Access Helpers ────────────────────────────────────────────────────────

def get_close(data, ticker):
    try:
        s = data["Close"][ticker].dropna()
        return s if len(s) >= 5 else None
    except Exception:
        return None


def get_ohlc(data, ticker):
    try:
        c = data["Close"][ticker].dropna()
        h = data["High"][ticker].dropna()
        l = data["Low"][ticker].dropna()
        if len(c) < 20:
            return None, None, None
        return h, l, c
    except Exception:
        return None, None, None


def pct_chg(series, periods):
    if series is None or len(series) <= periods:
        return None
    return (series.iloc[-1] / series.iloc[-periods] - 1) * 100


def ytd_chg(series):
    if series is None:
        return None
    try:
        y = series[series.index >= f"{datetime.now().year}-01-01"]
        if len(y) < 2:
            return None
        return (y.iloc[-1] / y.iloc[0] - 1) * 100
    except Exception:
        return None


def fmt_price(val, ticker=""):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    if ticker in ["^TNX", "^VIX", "^VIX3M"]:
        return f"{val:.2f}"
    if val > 10000:
        return f"{val:,.0f}"
    if val > 1000:
        return f"{val:,.2f}"
    if val > 10:
        return f"{val:.3f}"
    return f"{val:.5f}"


def fmt_pct(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


def vs_ma(price, ma):
    if ma is None or ma == 0:
        return "N/A"
    pct = (price / ma - 1) * 100
    arrow = "^" if pct >= 0 else "v"
    sign = "+" if pct >= 0 else ""
    return f"{arrow}{sign}{pct:.1f}%"


def table(headers, rows):
    """Render a plain-text aligned table."""
    all_rows = [headers] + rows
    widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(headers))]
    sep = "  " + "-+-".join("-" * w for w in widths)

    def fmt_row(row):
        return "  " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))

    lines = [fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


# ── Options Intelligence ───────────────────────────────────────────────────────

def get_options_data():
    lines = []
    for name, ticker_str in [("SPY", "SPY"), ("QQQ", "QQQ")]:
        try:
            t = yf.Ticker(ticker_str)
            exps = t.options
            if not exps:
                continue
            chain = t.option_chain(exps[0])
            put_vol = chain.puts["volume"].fillna(0).sum()
            call_vol = chain.calls["volume"].fillna(0).sum()
            put_oi = chain.puts["openInterest"].fillna(0).sum()
            call_oi = chain.calls["openInterest"].fillna(0).sum()
            pc_vol = put_vol / call_vol if call_vol > 0 else None
            pc_oi = put_oi / call_oi if call_oi > 0 else None

            sentiment = ""
            if pc_vol:
                if pc_vol > 1.2:
                    sentiment = " ->Elevated put buying (bearish lean)"
                elif pc_vol < 0.7:
                    sentiment = " ->Call dominated (bullish lean)"
                else:
                    sentiment = " ->Neutral"

            lines.append(f"  {name} P/C Volume ({exps[0]}): {pc_vol:.2f}{sentiment}" if pc_vol else f"  {name} P/C: N/A")
            lines.append(f"  {name} P/C Open Interest: {pc_oi:.2f}" if pc_oi else "")
        except Exception as e:
            lines.append(f"  {name} options: unavailable ({str(e)[:40]})")

    # VIX term structure
    try:
        vix_vals = {}
        for label, sym in [("VIX (1M)", "^VIX"), ("VIX3M (3M)", "^VIX3M")]:
            t = yf.Ticker(sym)
            info = t.fast_info
            if hasattr(info, "last_price") and info.last_price:
                vix_vals[label] = info.last_price
        if len(vix_vals) >= 2:
            vals = list(vix_vals.values())
            structure = "BACKWARDATION (near-term fear elevated)" if vals[0] > vals[-1] else "CONTANGO (normal)"
            lines.append("\n  VIX Term Structure:")
            for k, v in vix_vals.items():
                lines.append(f"    {k}: {v:.2f}")
            lines.append(f"    Structure: {structure}")
    except Exception:
        pass

    return [l for l in lines if l]


# ── Correlation Matrix ─────────────────────────────────────────────────────────

def get_correlations(data, window=30):
    assets = {
        "SPX": "^GSPC", "NDX": "^NDX", "Gold": "GC=F",
        "Silver": "SI=F", "WTI": "CL=F", "10Y": "^TNX",
        "VIX": "^VIX", "BTC": "BTC-USD", "HYG": "HYG", "DXY": "DX-Y.NYB",
    }
    closes = {}
    for name, ticker in assets.items():
        s = get_close(data, ticker)
        if s is not None and len(s) >= window:
            closes[name] = s.pct_change()

    if len(closes) < 4:
        return None

    df = pd.DataFrame(closes).dropna().tail(window)
    if len(df) < window // 2:
        return None
    return df.corr().round(2)


# ── Financial Datasets REST API ───────────────────────────────────────────────

def _fd_get(path):
    """Hit the financialdatasets.ai REST API and return parsed JSON or None."""
    if not FINANCIAL_DATASETS_API_KEY:
        return None
    url = f"https://api.financialdatasets.ai{path}"
    req = urllib.request.Request(url, headers={"X-API-KEY": FINANCIAL_DATASETS_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def get_fundamentals_block():
    """Fetch key fundamentals via yfinance Ticker.info (free, no API key needed)."""
    lines = []
    rows = []

    for ticker in FUNDAMENTAL_TICKERS:
        try:
            info = yf.Ticker(ticker).info
            if not info or info.get("trailingEps") is None:
                continue

            pe = info.get("trailingPE")
            fwd_pe = info.get("forwardPE")
            eps = info.get("trailingEps")
            eps_fwd = info.get("forwardEps")
            rev = info.get("totalRevenue")
            margin = info.get("profitMargins")
            target = info.get("targetMeanPrice")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            upside = ((target / price) - 1) * 100 if target and price else None

            rows.append([
                ticker,
                f"{pe:.1f}x" if pe else "N/A",
                f"{fwd_pe:.1f}x" if fwd_pe else "N/A",
                f"${eps:.2f}" if eps else "N/A",
                f"${eps_fwd:.2f}" if eps_fwd else "N/A",
                f"${rev/1e9:.0f}B" if rev else "N/A",
                f"{margin*100:.1f}%" if margin else "N/A",
                f"${target:.0f}" if target else "N/A",
                f"{upside:+.0f}%" if upside is not None else "N/A",
            ])
        except Exception:
            continue

    if rows:
        h = ["Ticker", "P/E", "Fwd P/E", "EPS TTM", "EPS Fwd", "Revenue", "Margin", "Analyst Target", "Upside"]
        lines.append(table(h, rows))
        lines.append("")
        lines.append("  Note: Analyst targets and forward P/E indicate sector valuation vs. macro regime.")
    else:
        lines.append("  Fundamental data unavailable (yfinance may be rate-limiting — retry later)")

    return lines


def get_earnings_results_block():
    """Fetch recent earnings surprise data via yfinance."""
    lines = []
    rows = []

    for ticker in FUNDAMENTAL_TICKERS:
        try:
            t = yf.Ticker(ticker)
            hist = t.earnings_history
            if hist is None or len(hist) == 0:
                continue
            latest = hist.iloc[-1]
            period = str(latest.name)[:7] if hasattr(latest, 'name') else "N/A"
            eps_est = latest.get("epsEstimate") if hasattr(latest, 'get') else latest["epsEstimate"]
            eps_act = latest.get("epsActual") if hasattr(latest, 'get') else latest["epsActual"]
            surprise_pct = latest.get("epsDifference") if hasattr(latest, 'get') else latest.get("epsDifference")
            if eps_act is None or pd.isna(eps_act):
                continue
            beat = "BEAT" if eps_act > eps_est else "MISS" if eps_act < eps_est else "IN-LINE"
            rows.append([
                ticker,
                period,
                f"${eps_est:.2f}" if eps_est and not pd.isna(eps_est) else "N/A",
                f"${eps_act:.2f}",
                beat,
                f"{surprise_pct:+.2f}" if surprise_pct and not pd.isna(surprise_pct) else "N/A",
            ])
        except Exception:
            continue

    if rows:
        h = ["Ticker", "Period", "EPS Est.", "EPS Act.", "Result", "Surprise $"]
        lines.append(table(h, rows))
        lines.append("")
        lines.append("  Note: Earnings beat/miss streaks signal sector momentum and institutional flows.")
    else:
        lines.append("  Earnings history unavailable via yfinance")

    return lines


# ── Main Data Block Builder ────────────────────────────────────────────────────

def build_data_block(data):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = []

    out.append("=" * 72)
    out.append("  PRE-FETCHED MARKET DATA")
    out.append(f"  Generated: {now} | Source: yfinance (Yahoo Finance)")
    out.append("")
    out.append("  INSTRUCTIONS FOR CLAUDE:")
    out.append("  - Use this data as PRIMARY source for all prices and technicals")
    out.append("  - Do NOT search for prices or asset levels — they are here")
    out.append("  - Use WebSearch ONLY for: today's news, geopolitical events,")
    out.append("    economic calendar, and analyst commentary")
    out.append("=" * 72)

    # ── 1. Core Assets ──
    out.append("\n### 1. CORE ASSETS — PRICES & PERFORMANCE\n")
    h = ["Asset", "Price", "1D%", "5D%", "1M%", "YTD%", "52W High", "52W Low"]
    rows = []
    for name, ticker in CORE_ASSETS.items():
        s = get_close(data, ticker)
        if s is None:
            rows.append([name] + ["N/A"] * 7)
            continue
        price = s.iloc[-1]
        rows.append([
            name,
            fmt_price(price, ticker),
            fmt_pct(pct_chg(s, 1)),
            fmt_pct(pct_chg(s, 5)),
            fmt_pct(pct_chg(s, 21)),
            fmt_pct(ytd_chg(s)),
            fmt_price(s.tail(252).max(), ticker),
            fmt_price(s.tail(252).min(), ticker),
        ])
    out.append(table(h, rows))

    # ── 2. Technical Indicators ──
    out.append("\n### 2. TECHNICAL INDICATORS (Daily)\n")
    tech_assets = {**CORE_ASSETS, "ETH": "ETH-USD", "Copper": "HG=F"}
    skip_tech = {"^VIX", "^TNX"}  # volatility/yield: technicals less meaningful

    th = ["Asset", "Price", "vs SMA20", "vs SMA50", "vs SMA200", "RSI(14)", "MACD", "BB%B", "ATR%"]
    trows = []
    for name, ticker in tech_assets.items():
        if ticker in skip_tech:
            continue
        high, low, close = get_ohlc(data, ticker)
        if close is None:
            continue
        price = close.iloc[-1]
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

        try:
            rsi_val = rsi_label(calc_rsi(close))
        except Exception:
            rsi_val = "N/A"

        try:
            _, _, hist = calc_macd(close)
            macd_str = macd_label(hist)
        except Exception:
            macd_str = "N/A"

        try:
            pctb = pctb_label(calc_bollinger_pctb(close))
        except Exception:
            pctb = "N/A"

        try:
            atr_val = calc_atr(high, low, close) if high is not None else None
            atr_str = f"{(atr_val / price * 100):.2f}%" if atr_val else "N/A"
        except Exception:
            atr_str = "N/A"

        trows.append([
            name,
            fmt_price(price, ticker),
            vs_ma(price, sma20),
            vs_ma(price, sma50),
            vs_ma(price, sma200) if sma200 else "N/A",
            rsi_val,
            macd_str,
            pctb,
            atr_str,
        ])
    out.append(table(th, trows))

    # ── 3. Sector Performance ──
    out.append("\n### 3. SECTOR ETF PERFORMANCE (relative to SPX)\n")
    spx = get_close(data, "^GSPC")
    spx_1d = pct_chg(spx, 1)
    spx_5d = pct_chg(spx, 5)
    spx_21d = pct_chg(spx, 21)

    def rel(asset_pct, bench_pct):
        if asset_pct is None or bench_pct is None:
            return "N/A"
        diff = asset_pct - bench_pct
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.2f}%"

    sh = ["Sector", "Price", "1D%", "Rel 1D", "5D%", "Rel 5D", "1M%", "Rel 1M"]
    srows = []
    for name, ticker in SECTORS.items():
        s = get_close(data, ticker)
        if s is None:
            continue
        d1 = pct_chg(s, 1)
        d5 = pct_chg(s, 5)
        d21 = pct_chg(s, 21)
        srows.append([
            name, fmt_price(s.iloc[-1]),
            fmt_pct(d1), rel(d1, spx_1d),
            fmt_pct(d5), rel(d5, spx_5d),
            fmt_pct(d21), rel(d21, spx_21d),
        ])
    out.append(table(sh, srows))

    # ── 4. Global Indices & Commodities ──
    out.append("\n### 4. GLOBAL INDICES & COMMODITIES\n")
    gh = ["Asset", "Price", "1D%", "5D%", "1M%", "YTD%"]
    grows = []
    for name, ticker in GLOBAL_INDICES.items():
        s = get_close(data, ticker)
        if s is None:
            continue
        grows.append([
            name, fmt_price(s.iloc[-1], ticker),
            fmt_pct(pct_chg(s, 1)), fmt_pct(pct_chg(s, 5)),
            fmt_pct(pct_chg(s, 21)), fmt_pct(ytd_chg(s)),
        ])
    out.append(table(gh, grows))

    # ── 5. Fixed Income, FX & Credit ──
    out.append("\n### 5. FIXED INCOME, FX & CREDIT\n")
    firows = []
    for name, ticker in FIXED_INCOME_FX.items():
        s = get_close(data, ticker)
        if s is None:
            continue
        firows.append([
            name, fmt_price(s.iloc[-1], ticker),
            fmt_pct(pct_chg(s, 1)), fmt_pct(pct_chg(s, 5)),
            fmt_pct(pct_chg(s, 21)), fmt_pct(ytd_chg(s)),
        ])
    out.append(table(gh, firows))

    # ── 6. Crypto Extended ──
    out.append("\n### 6. CRYPTO (Extended)\n")
    ch = ["Asset", "Price", "1D%", "5D%", "1M%", "YTD%", "RSI(14)"]
    crows = []
    for name, ticker in CRYPTO_EXTENDED.items():
        s = get_close(data, ticker)
        if s is None:
            continue
        try:
            rsi_str = rsi_label(calc_rsi(s))
        except Exception:
            rsi_str = "N/A"
        crows.append([
            name, fmt_price(s.iloc[-1]),
            fmt_pct(pct_chg(s, 1)), fmt_pct(pct_chg(s, 5)),
            fmt_pct(pct_chg(s, 21)), fmt_pct(ytd_chg(s)),
            rsi_str,
        ])
    out.append(table(ch, crows))

    # ── 7. Cross-Asset Correlations ──
    out.append("\n### 7. CROSS-ASSET CORRELATIONS (30-Day Rolling)\n")
    corr = get_correlations(data)
    if corr is not None:
        cols = list(corr.columns)
        name_w = max(len(c) for c in cols)
        cell_w = 6
        header_line = "  " + " " * name_w + " | " + " | ".join(c.rjust(cell_w) for c in cols)
        out.append(header_line)
        out.append("  " + "-" * (len(header_line) - 2))
        for c in cols:
            vals = " | ".join(f"{corr.loc[c, c2]:.2f}".rjust(cell_w) for c2 in cols)
            out.append(f"  {c.ljust(name_w)} | {vals}")
        out.append("\n  Interpretation notes:")
        out.append("  - SPX/VIX near -1.0 = fear gauge normal; divergence = structural shift")
        out.append("  - Gold/DXY negative = dollar-driven gold; positive = pure risk-off flight")
        out.append("  - SPX/HYG divergence = credit stress forming ahead of equity selloff")
    else:
        out.append("  Correlation data unavailable (insufficient history)")

    # ── 8. Options Intelligence ──
    out.append("\n### 8. OPTIONS MARKET INTELLIGENCE\n")
    opt_lines = get_options_data()
    if opt_lines:
        out.extend(opt_lines)
    else:
        out.append("  Options data unavailable")

    # ── 9. Key Technical Levels ──
    out.append("\n### 9. KEY TECHNICAL LEVELS\n")
    level_assets = [
        ("SPX", "^GSPC"), ("NDX", "^NDX"), ("Gold", "GC=F"),
        ("Silver", "SI=F"), ("WTI", "CL=F"), ("BTC", "BTC-USD"),
        ("EUR/USD", "EURUSD=X"), ("DXY", "DX-Y.NYB"),
    ]
    for name, ticker in level_assets:
        s = get_close(data, ticker)
        if s is None or len(s) < 20:
            continue
        price = s.iloc[-1]
        sma20 = s.rolling(20).mean().iloc[-1]
        sma50 = s.rolling(50).mean().iloc[-1]
        sma200 = s.rolling(200).mean().iloc[-1] if len(s) >= 200 else None
        high_20 = s.tail(20).max()
        low_20 = s.tail(20).min()

        signals = []
        if price > sma20:
            signals.append("above SMA20")
        else:
            signals.append("below SMA20")
        if price > sma50:
            signals.append("above SMA50")
        else:
            signals.append("below SMA50")
        if sma200:
            signals.append("above SMA200 [bull]" if price > sma200 else "below SMA200 [bear]")

        ma_str = f"SMA20={fmt_price(sma20, ticker)}  SMA50={fmt_price(sma50, ticker)}"
        if sma200:
            ma_str += f"  SMA200={fmt_price(sma200, ticker)}"

        out.append(f"  {name} @ {fmt_price(price, ticker)}:")
        out.append(f"    {ma_str}")
        out.append(f"    20D Range: {fmt_price(low_20, ticker)} — {fmt_price(high_20, ticker)}")
        out.append(f"    Trend: {', '.join(signals)}")

    # ── 10. Key Company Fundamentals ──
    out.append("\n### 10. KEY COMPANY FUNDAMENTALS (TTM via financialdatasets.ai)\n")
    out.append("  [Major bellwethers — use for macro earnings health, not stock picks]\n")
    fund_lines = get_fundamentals_block()
    out.extend(fund_lines)

    # ── 11. Latest Earnings Results ──
    out.append("\n### 11. LATEST QUARTERLY EARNINGS — ACTUAL vs ESTIMATE\n")
    out.append("  [Beat/miss momentum signals sector health and rotation]\n")
    earn_lines = get_earnings_results_block()
    if earn_lines:
        out.extend(earn_lines)
    else:
        out.append("  Earnings data unavailable")

    out.append("\n" + "=" * 72)
    out.append("  END PRE-FETCHED DATA")
    out.append("=" * 72 + "\n")

    return "\n".join(out)


def generate_data_block():
    """Fetch all market data and return formatted block string."""
    print("[MarketData] Downloading data via yfinance...")
    try:
        data = yf.download(
            _ALL_TICKERS,
            period="12mo",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        print(f"[MarketData] Downloaded {len(data)} rows")
        return build_data_block(data)
    except Exception as e:
        return f"[MarketData ERROR: {e}]\n\nFall back to WebSearch for all market data.\n"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(generate_data_block())
