import streamlit as st
import pandas as pd
import pyotp
from SmartApi import SmartConnect
import requests
import datetime
import ta

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Swing Option Engine", layout="wide")
st.title("📈 Institutional Swing Option Engine")

# ---------- SECRETS ----------
API_KEY = st.secrets["API_KEY"]
CLIENT_ID = st.secrets["CLIENT_ID"]
PASSWORD = st.secrets["PASSWORD"]
TOTP_SECRET = st.secrets["TOTP_SECRET"]

# ---------- LOGIN ----------
@st.cache_resource
def angel_login():
    obj = SmartConnect(api_key=API_KEY)
    otp = pyotp.TOTP(TOTP_SECRET).now()
    data = obj.generateSession(CLIENT_ID, PASSWORD, otp)
    return obj

smart = angel_login()

# ---------- INPUT SECTION ----------
st.sidebar.header("Trade Settings")

capital = st.sidebar.number_input("Enter Capital ₹", value=20000)
underlying = st.sidebar.selectbox(
    "Select Underlying",
    ["NIFTY", "BANKNIFTY", "Top 5 Stocks", "Custom"]
)

if underlying == "Custom":
    custom_symbol = st.sidebar.text_input("Enter Stock Symbol (Example: SBIN)")
else:
    custom_symbol = None

risk_percent = st.sidebar.slider("Risk % Per Trade", 1, 5, 1)

# ---------- ANALYSIS FUNCTION ----------
def analyze(symbol, token, exchange="NSE"):
    to_date = datetime.datetime.now()
    from_date = to_date - datetime.timedelta(days=10)

    data = smart.getCandleData({
        "exchange": exchange,
        "symboltoken": token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M")
    })

    df = pd.DataFrame(data["data"], columns=["time","open","high","low","close","volume"])
    df["close"] = df["close"].astype(float)

    df["ema20"] = ta.trend.ema_indicator(df["close"], 20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], 50)
    df["rsi"] = ta.momentum.rsi(df["close"], 14)

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

    if call_score > put_score:
        direction = "CALL"
    elif put_score > call_score:
        direction = "PUT"
    else:
        direction = "NO TRADE"

    return direction, latest["close"]

# ---------- MAIN BUTTON ----------
if st.button("🚀 Generate Trade Plan"):

    try:

        if underlying == "NIFTY":
            token = "99926000"
            direction, spot = analyze("NIFTY", token)

        elif underlying == "BANKNIFTY":
            token = "99926009"
            direction, spot = analyze("BANKNIFTY", token)

        elif underlying == "Top 5 Stocks":
            stocks = ["RELIANCE-EQ","HDFCBANK-EQ","ICICIBANK-EQ","TCS-EQ","INFY-EQ"]
            best_signal = None
            best_symbol = None
            best_spot = None

            for s in stocks:
                search = smart.searchScrip("NSE", s.split("-")[0])
                token = search["data"][3]["symboltoken"]
                d, sp = analyze(s, token)

                if d != "NO TRADE":
                    best_signal = d
                    best_symbol = s.split("-")[0]
                    best_spot = sp
                    break

            direction = best_signal
            spot = best_spot
            underlying = best_symbol

        elif underlying == "Custom" and custom_symbol:
            search = smart.searchScrip("NSE", custom_symbol)
            token = search["data"][3]["symboltoken"]
            direction, spot = analyze(custom_symbol, token)

        if direction == "NO TRADE":
            st.warning("No strong setup found.")
            st.stop()

        st.subheader("📊 Spot Analysis")
        st.write("Direction:", direction)
        st.write("Spot Price:", spot)

        st.success("Signal Generated Successfully ✅")

    except Exception as e:
        st.error("Error:", e)
