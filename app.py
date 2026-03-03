import streamlit as st
from SmartApi import SmartConnect
import pyotp
import pandas as pd
import ta
from datetime import datetime, timedelta
import requests
import math

# ================= PAGE =================

st.set_page_config(page_title="Institutional Swing Option Engine", layout="wide")
st.title("📈 Institutional Swing Option Engine")

# ================= SECRETS =================

API_KEY = st.secrets["API_KEY"]
CLIENT_ID = st.secrets["CLIENT_ID"]
PASSWORD = st.secrets["PASSWORD"]
TOTP_SECRET = st.secrets["TOTP_SECRET"]

# ================= LOGIN =================

@st.cache_resource
def angel_login():
    smartApi = SmartConnect(api_key=API_KEY)
    otp = pyotp.TOTP(TOTP_SECRET).now()
    session = smartApi.generateSession(CLIENT_ID, PASSWORD, otp)
    return smartApi

smartApi = angel_login()

# ================= SIDEBAR INPUT =================

st.sidebar.header("Trade Settings")

capital = st.sidebar.number_input("Enter Your Trading Capital ₹", value=20000.0)

choice = st.sidebar.selectbox(
    "Select Underlying",
    ["NIFTY", "BANKNIFTY", "Top 5 Stocks", "Custom Stock"]
)

if choice == "Custom Stock":
    custom = st.sidebar.text_input("Enter Stock Symbol (example SBIN)")
else:
    custom = None

# ================= SYMBOL SELECTION =================

top5 = ["RELIANCE", "HDFCBANK", "ICICIBANK", "TCS", "INFY"]

if choice == "NIFTY":
    symbols = ["NIFTY"]
elif choice == "BANKNIFTY":
    symbols = ["BANKNIFTY"]
elif choice == "Top 5 Stocks":
    symbols = top5
elif choice == "Custom Stock" and custom:
    symbols = [custom.upper()]
else:
    symbols = []

index_tokens = {
    "NIFTY": "99926000",
    "BANKNIFTY": "99926009"
}

# ================= ANALYSIS FUNCTION =================

def analyze_symbol(symbol):

    if symbol in index_tokens:
        token = index_tokens[symbol]
        exchange = "NSE"
    else:
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
        exchange = "NSE"

    # DAILY
    daily = smartApi.getCandleData({
        "exchange": exchange,
        "symboltoken": token,
        "interval": "ONE_DAY",
        "fromdate": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d %H:%M"),
        "todate": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    if "data" not in daily or not daily["data"]:
        return None

    df_daily = pd.DataFrame(daily["data"], columns=["t","o","h","l","c","v"])
    df_daily["c"] = df_daily["c"].astype(float)
    df_daily["ema20"] = ta.trend.ema_indicator(df_daily["c"],20)
    df_daily["ema50"] = ta.trend.ema_indicator(df_daily["c"],50)

    daily_latest = df_daily.iloc[-1]

    if daily_latest["ema20"] > daily_latest["ema50"]:
        trend = "BULLISH"
    elif daily_latest["ema20"] < daily_latest["ema50"]:
        trend = "BEARISH"
    else:
        return None

    # INTRADAY
    intra = smartApi.getCandleData({
        "exchange": exchange,
        "symboltoken": token,
        "interval": "FIVE_MINUTE",
        "fromdate": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        "todate": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    if "data" not in intra or not intra["data"]:
        return None

    df = pd.DataFrame(intra["data"], columns=["t","o","h","l","c","v"])
    df = df.astype({"c":float,"h":float,"l":float,"v":float})

    df["ema20"] = ta.trend.ema_indicator(df["c"],20)
    df["ema50"] = ta.trend.ema_indicator(df["c"],50)
    df["rsi"] = ta.momentum.rsi(df["c"],14)
    df["avg_vol"] = df["v"].rolling(20).mean()
    df["atr"] = ta.volatility.average_true_range(df["h"],df["l"],df["c"],14)

    latest = df.iloc[-1]

    call_score = 0
    put_score = 0

    if latest["ema20"] > latest["ema50"]:
        call_score += 1
    else:
        put_score += 1

    if latest["rsi"] > 55:
        call_score += 1
    elif latest["rsi"] < 45:
        put_score += 1

    high20 = df["h"].rolling(20).max().iloc[-2]
    low20 = df["l"].rolling(20).min().iloc[-2]

    if latest["c"] > high20:
        call_score += 1
    elif latest["c"] < low20:
        put_score += 1

    if latest["v"] > 1.5 * latest["avg_vol"]:
        if call_score > put_score:
            call_score += 1
        else:
            put_score += 1

    if trend == "BULLISH" and call_score >= 2:
        direction = "CALL"
        score = call_score
    elif trend == "BEARISH" and put_score >= 2:
        direction = "PUT"
        score = put_score
    else:
        return None

    return {
        "symbol": symbol,
        "direction": direction,
        "score": score,
        "spot": latest["c"],
        "atr": latest["atr"]
    }

# ================= MAIN BUTTON =================

if st.button("🚀 Generate Trade Plan"):

    best = None

    for s in symbols:
        r = analyze_symbol(s)
        if r:
            if not best or r["score"] > best["score"]:
                best = r

    if not best:
        st.warning("No setup found.")
        st.stop()

    # RISK
    if best["score"] >= 4:
        risk_percent = 3
        label = "STRONG"
    elif best["score"] == 3:
        risk_percent = 2
        label = "GOOD"
    else:
        risk_percent = 1
        label = "WEAK"

    risk_amount = capital * (risk_percent/100)

    # OPTION MASTER
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    master = requests.get(url).json()
    options = pd.DataFrame(master)

    symbol = best["symbol"]

    if symbol in ["NIFTY","BANKNIFTY"]:
        options = options[(options["name"]==symbol) & (options["instrumenttype"]=="OPTIDX")]
    else:
        options = options[(options["name"]==symbol) & (options["instrumenttype"]=="OPTSTK")]

    options["expiry"] = pd.to_datetime(options["expiry"], errors="coerce")
    options = options.dropna(subset=["expiry"])

    nearest = options[options["expiry"]>=datetime.now()]["expiry"].min()
    options = options[options["expiry"]==nearest]

    options["strike"] = pd.to_numeric(options["strike"],errors="coerce")/100

    spot = best["spot"]

    unique_strikes = sorted(options["strike"].unique())
    step = min([abs(unique_strikes[i+1]-unique_strikes[i]) for i in range(len(unique_strikes)-1)])

    atm = round(spot/step)*step
    option_type = "CE" if best["direction"]=="CALL" else "PE"

    final = options[(options["strike"]==atm) &
                    (options["symbol"].str.endswith(option_type))].iloc[0]

    ltp = smartApi.ltpData(final["exch_seg"], final["symbol"], final["token"])
    premium = ltp["data"]["ltp"]
    lot_size = int(final["lotsize"])

    premium_stop = premium * 0.5
    risk_per_lot = premium_stop * lot_size

    lots = math.floor(risk_amount / risk_per_lot)
    warning = False

    if lots < 1:
        warning = True
        lots = 1

    total_qty = lots * lot_size
    capital_required = premium * total_qty
    max_loss = risk_per_lot * lots
    target_premium = premium * 1.5
    potential_profit = (target_premium - premium) * total_qty

    # OUTPUT
    st.subheader("📊 Final Trade Plan")

    st.write("Underlying:", symbol)
    st.write("Direction:", best["direction"])
    st.write("Strength:", label)
    st.write("Spot:", round(spot,2))
    st.write("Expiry:", nearest.date())
    st.write("Strike:", atm)
    st.write("Option Type:", option_type)
    st.write("Premium:", premium)
    st.write("Lot Size:", lot_size)
    st.write("Lots To Buy:", lots)
    st.write("Total Quantity:", total_qty)
    st.write("Capital Required:", round(capital_required,2))
    st.write("Ideal Risk Allowed:", round(risk_amount,2))
    st.write("Actual Risk Taking:", round(max_loss,2))
    st.write("Target Premium:", round(target_premium,2))
    st.write("Potential Profit:", round(potential_profit,2))

    if warning:
        st.error("⚠ Capital too small for proper risk sizing.")
