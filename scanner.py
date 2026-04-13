"""
NSE Weekly Low Scanner — GitHub Actions version
Reads symbols from symbols.txt, writes output/data.json + output/data.csv
"""

import pandas as pd
import yfinance as yf
import json, time, os
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SYMBOLS_FILE = "symbols.txt"
OUTPUT_DIR   = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── RSI (Wilder) ─────────────────────────────────────────────────────────────
def calculate_rsi(closes, period=14):
    try:
        s = pd.Series(closes).dropna()
        if len(s) < period + 1:
            return None
        delta = s.diff()
        gain  = delta.clip(lower=0)
        loss  = -delta.clip(upper=0)
        ag = gain.ewm(alpha=1/period, adjust=False).mean()
        al = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = ag / al
        return round((100 - 100 / (1 + rs)).iloc[-1], 2)
    except:
        return None

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def pct_change(new, old):
    try:
        if pd.isna(new) or pd.isna(old) or old == 0:
            return None
        return round(((float(new) - float(old)) / float(old)) * 100, 2)
    except:
        return None

def fetch_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# ─── READ SYMBOLS ─────────────────────────────────────────────────────────────
with open(SYMBOLS_FILE) as f:
    symbols = [line.strip().upper() for line in f if line.strip() and not line.startswith('#')]

print(f"Processing {len(symbols)} symbols...")

output_rows = []

for symbol in symbols:
    ticker = f"{symbol}.NS"
    print(f"  {symbol}...", end=" ")

    df = fetch_data(ticker)
    if df.empty or len(df) < 30:
        print("SKIP (no data)")
        continue

    try:
        df = df.reset_index()
        df["Date"]  = pd.to_datetime(df["Date"])
        df["Low"]   = pd.to_numeric(df["Low"],   errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.sort_values("Date").dropna(subset=["Low","Close"])

        rsi_14 = calculate_rsi(df["Close"].tolist())

        last_close    = float(df["Close"].iloc[-1])
        last_day_low  = float(df["Low"].iloc[-1])

        df["Week"] = df["Date"].dt.to_period("W-FRI")
        weeks = df["Week"].drop_duplicates().sort_values()

        if len(weeks) < 4:
            print("SKIP (< 4 weeks)")
            continue

        def wdf(w): return df[df["Week"] == w]

        df_w3   = wdf(weeks.iloc[-4])
        df_w2   = wdf(weeks.iloc[-3])
        df_w1   = wdf(weeks.iloc[-2])
        df_curr = wdf(weeks.iloc[-1])

        low_w3   = float(df_w3["Low"].min())
        low_w2   = float(df_w2["Low"].min())
        low_w1   = float(df_w1["Low"].min())
        low_curr = float(df_curr["Low"].min())

        break_w3   = "Yes" if (df_w2["Low"]   < low_w3).any()   else "No"
        break_w2   = "Yes" if (df_w1["Low"]   < low_w2).any()   else "No"
        break_w1   = "Yes" if (df_curr["Low"] < low_w1).any()   else "No"
        break_curr = "Yes" if last_close < low_curr              else "No"

        close_w3   = float(df_w3["Close"].iloc[-1])
        close_w2   = float(df_w2["Close"].iloc[-1])
        close_w1   = float(df_w1["Close"].iloc[-1])
        close_curr = float(df_curr["Close"].iloc[-1])

        row = {
            "symbol":    symbol,
            "w3l":       round(low_w3,   2),
            "w2l":       round(low_w2,   2),
            "w1l":       round(low_w1,   2),
            "cwl":       round(low_curr, 2),
            "w3lb":      break_w3,
            "w2lb":      break_w2,
            "w1lb":      break_w1,
            "bc":        break_curr,
            "w3ch":      pct_change(close_w2,   close_w3),
            "w2ch":      pct_change(close_w1,   close_w2),
            "w1ch":      pct_change(close_curr, close_w1),
            "ldc":       round(last_close,   2),
            "ldl":       round(last_day_low, 2),
            "diff_fwl":  pct_change(last_close, low_w1),
            "diff_fldl": pct_change(last_close, last_day_low),
            "rsi14":     rsi_14,
        }
        output_rows.append(row)
        print("OK")
        time.sleep(0.3)

    except Exception as e:
        print(f"ERROR: {e}")

# ─── WRITE JSON ───────────────────────────────────────────────────────────────
meta = {
    "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "total":      len(output_rows),
    "data":       output_rows
}
with open(f"{OUTPUT_DIR}/data.json", "w") as f:
    json.dump(meta, f, indent=2)

# ─── WRITE CSV ────────────────────────────────────────────────────────────────
if output_rows:
    pd.DataFrame(output_rows).to_csv(f"{OUTPUT_DIR}/data.csv", index=False)

print(f"\n✅ Done — {len(output_rows)} stocks written to {OUTPUT_DIR}/")
