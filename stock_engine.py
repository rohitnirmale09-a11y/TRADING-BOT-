import pandas as pd
import ta
import time
from datetime import datetime, timedelta


def analyze_stock(smartApi, symbol):

    try:

        # ===== FIND TOKEN =====
        search = smartApi.searchScrip("NSE", symbol)

        if "data" not in search or not search["data"]:
            return None

        eq_symbol = None

        for item in search["data"]:
            if item["tradingsymbol"].endswith("-EQ"):
                eq_symbol = item
                break

        if not eq_symbol:
            return None

        token = eq_symbol["symboltoken"]


        # ===== RATE LIMIT PROTECTION =====
        time.sleep(0.12)


        # ===== FETCH CANDLE DATA =====
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
            "l": float,
            "v": float
        })


        # ===== INDICATORS =====

        df["ema20"] = ta.trend.ema_indicator(df["c"], 20)
        df["ema50"] = ta.trend.ema_indicator(df["c"], 50)

        df["rsi"] = ta.momentum.rsi(df["c"], 14)

        df["avg_vol"] = df["v"].rolling(20).mean()

        df["atr"] = ta.volatility.average_true_range(df["h"], df["l"], df["c"], 14)


        latest = df.iloc[-1]


        # ===== VOLATILITY =====

        atr = latest["atr"] if not pd.isna(latest["atr"]) else 0

        if atr == 0:
            volatility = "UNKNOWN"
        else:
            atr_percent = atr / latest["c"]
            if atr_percent > 0.04:
                volatility = "HIGH"
            elif atr_percent > 0.002:
                volatility = "MEDIUM"
            else:
                volatility = "LOW"


        call_score = 0
        put_score = 0


        # ===== AI WEIGHTS =====

        TREND_WEIGHT = 2
        BREAKOUT_WEIGHT = 2
        VOLUME_WEIGHT = 1
        RSI_WEIGHT = 1


        # ===== TREND =====

        if latest["ema20"] > latest["ema50"]:
            call_score += TREND_WEIGHT
        else:
            put_score += TREND_WEIGHT


        # ===== RSI =====

        if latest["rsi"] > 55:
            call_score += RSI_WEIGHT

        if latest["rsi"] < 45:
            put_score += RSI_WEIGHT


        # ===== BREAKOUT =====

        high20 = df["h"].rolling(20).max().iloc[-2]
        low20 = df["l"].rolling(20).min().iloc[-2]

        if latest["c"] > high20:
            call_score += BREAKOUT_WEIGHT

        if latest["c"] < low20:
            put_score += BREAKOUT_WEIGHT

        # ===== SMART MONEY LIQUIDITY SWEEP =====

        prev_high = df["h"].rolling(20).max().iloc[-2]
        prev_low = df["l"].rolling(20).min().iloc[-2]

        if latest["h"] > prev_high and latest["c"] < prev_high:
            put_score += 2

        if latest["l"] < prev_low and latest["c"] > prev_low:
            call_score += 2

        # ===== SMART MONEY ZONE =====

        zone = "NONE"

        body = abs(latest["c"] - latest["o"])

        if body > (latest["atr"] * 1.5):

            if latest["c"] > latest["o"]:
                zone = "DEMAND"
                call_score += 1

            else:
                zone = "SUPPLY"
                put_score += 1

        # ===== VOLUME SPIKE =====

        if latest["v"] > 1.5 * latest["avg_vol"]:
            call_score += VOLUME_WEIGHT


        # ===== LIVE PRICE =====

        try:

            ltp_data = smartApi.ltpData(
                "NSE",
                eq_symbol["tradingsymbol"],
                token
            )

            if "data" in ltp_data and "ltp" in ltp_data["data"]:
                spot = float(ltp_data["data"]["ltp"])
            else:
                spot = float(latest["c"])

        except:
            spot = float(latest["c"])


        # ===== FINAL SIGNAL =====

        max_score = 10


        if call_score > put_score:

            probability = round((call_score / max_score) * 100)

            return {
                "symbol": symbol,
                "direction": "CALL",
                "score": call_score,
                "probability": probability,
                "spot": spot,
                "volatility": volatility,
                "smart_zone": zone  
            }


        elif put_score > call_score:

            probability = round((put_score / max_score) * 100)

            return {
                "symbol": symbol,
                "direction": "PUT",
                "score": put_score,
                "probability": probability,
                "spot": spot,
                "volatility": volatility,
                "smart_zone": zone
            }


        return None


    except:
        return None