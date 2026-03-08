import pandas as pd
import ta
from datetime import datetime, timedelta


# ================= INDEX TOKENS =================

index_tokens = {

    "NIFTY": "99926000",
    "BANKNIFTY": "99926009"

}


# ================= INDEX ANALYSIS =================

def analyze_index(smartApi, symbol):

    token = index_tokens[symbol]

    candles = smartApi.getCandleData({

        "exchange": "NSE",
        "symboltoken": token,
        "interval": "FIVE_MINUTE",

        "fromdate": (datetime.now()-timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        "todate": datetime.now().strftime("%Y-%m-%d %H:%M")

    })

    if "data" not in candles or not candles["data"]:
        return None


    # ===== DATAFRAME =====

    df = pd.DataFrame(
        candles["data"],
        columns=["t","o","h","l","c","v"]
    )

    df = df.astype({
        "c": float,
        "h": float,
        "l": float
    })


    # ===== INDICATORS =====

    df["ema20"] = ta.trend.ema_indicator(df["c"], 20)
    df["ema50"] = ta.trend.ema_indicator(df["c"], 50)

    df["rsi"] = ta.momentum.rsi(df["c"], 14)


    latest = df.iloc[-1]

    call_score = 0
    put_score = 0


    # ===== TREND =====

    if latest["ema20"] > latest["ema50"]:
        call_score += 1
    else:
        put_score += 1


    # ===== RSI =====

    if latest["rsi"] > 55:
        call_score += 1

    if latest["rsi"] < 45:
        put_score += 1


    # ===== FINAL SIGNAL =====

    if call_score >= 2:

        return {

            "symbol": symbol,
            "direction": "CALL",
            "score": call_score,
            "spot": latest["c"]

        }

    if put_score >= 2:

        return {

            "symbol": symbol,
            "direction": "PUT",
            "score": put_score,
            "spot": latest["c"]

        }

    return None