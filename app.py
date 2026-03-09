import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from datetime import datetime, timedelta

from angel_login import angel_login
from scanner import run_scanner
from sector_strength import sectors, analyze_sector
from option_selector import select_option
from stock_engine import analyze_stock
from institutional_flow import analyze_institutional_flow
from index_engine import analyze_index


# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI Swing Option Engine",
    page_icon="📈",
    layout="wide"
)

# ================= DARK TRADING THEME =================

st.markdown("""
<style>

.stApp {
    background-color:#0f172a;
    color:white;
}

[data-testid="stSidebar"] {
    background-color:#111827;
}

.metric-card {
    background-color:#1e293b;
    padding:20px;
    border-radius:10px;
    text-align:center;
}

.call {
    color:#22c55e;
    font-weight:bold;
}

.put {
    color:#ef4444;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

st.title("📈 AI Swing Option Trading Dashboard")
st.caption("Institutional Style Swing Trading Scanner")


# ================= LOGIN =================

@st.cache_resource
def login():
    return angel_login()

smartApi = login()


# ================= SIDEBAR =================

st.sidebar.title("Trading Controls")

mode = st.sidebar.selectbox(
    "Select Mode",
    [
        "F&O Market Scanner",
        "NIFTY Analysis",
        "BANKNIFTY Analysis",
        "Custom Stock Analysis"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
"""
Scanner Includes

• Institutional Flow  
• Sector Strength  
• Trend + RSI  
• Liquidity Sweep  
• Smart Money Zones  
• ATR Volatility
"""
)


# ================= PROBABILITY GAUGE =================

def probability_gauge(prob):

    bars = int(prob / 5)
    gauge = "█"*bars + "░"*(20-bars)

    st.markdown(f"""
**Signal Strength**

`[{gauge}] {prob}%`
""")


# ================= AI TRADE EXPLANATION =================

def ai_trade_explanation(direction, zone, volatility):

    st.markdown("### 🧠 AI Trade Explanation")

    if direction == "CALL":
        st.write("✔ Trend: EMA20 above EMA50 (bullish trend)")
        st.write("✔ Momentum: RSI indicates buying pressure")
        st.write("✔ Breakout: Price moving above resistance")
    else:
        st.write("✔ Trend: EMA20 below EMA50 (bearish trend)")
        st.write("✔ Momentum: RSI indicates selling pressure")
        st.write("✔ Breakdown: Price moving below support")

    st.write("✔ Smart Money Zone:", zone)
    st.write("✔ Volatility:", volatility)


# ================= INDICATOR CHART =================

def indicator_chart(smartApi, symbol, zone):

    search = smartApi.searchScrip("NSE", symbol)

    if "data" not in search or not search["data"]:
        return

    token = None

    for item in search["data"]:
        if item["tradingsymbol"].endswith("-EQ"):
            token = item["symboltoken"]

    if not token:
        return

    candles = smartApi.getCandleData({

        "exchange": "NSE",
        "symboltoken": token,
        "interval": "FIVE_MINUTE",

        "fromdate": (datetime.now()-timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        "todate": datetime.now().strftime("%Y-%m-%d %H:%M")

    })

    if "data" not in candles:
        return

    df = pd.DataFrame(
        candles["data"],
        columns=["t","o","h","l","c","v"]
    )

    df = df.astype({
        "o":float,
        "h":float,
        "l":float,
        "c":float,
        "v":float
    })

    df["ema20"] = ta.trend.ema_indicator(df["c"],20)
    df["ema50"] = ta.trend.ema_indicator(df["c"],50)
    df["rsi"] = ta.momentum.rsi(df["c"],14)

    high20 = df["h"].rolling(20).max()
    low20 = df["l"].rolling(20).min()

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6,0.2,0.2],
        vertical_spacing=0.03
    )

    fig.add_trace(go.Candlestick(
        x=df["t"], open=df["o"], high=df["h"],
        low=df["l"], close=df["c"], name="Price"),
        row=1,col=1)

    fig.add_trace(go.Scatter(
        x=df["t"],y=df["ema20"],line=dict(color="blue"),name="EMA20"),
        row=1,col=1)

    fig.add_trace(go.Scatter(
        x=df["t"],y=df["ema50"],line=dict(color="orange"),name="EMA50"),
        row=1,col=1)

    fig.add_trace(go.Scatter(
        x=df["t"],y=high20,line=dict(color="green",dash="dot"),
        name="Breakout High"), row=1,col=1)

    fig.add_trace(go.Scatter(
        x=df["t"],y=low20,line=dict(color="red",dash="dot"),
        name="Breakout Low"), row=1,col=1)

    if zone == "SUPPLY":
        fig.add_hrect(
            y0=df["h"].max()*0.98,
            y1=df["h"].max(),
            fillcolor="red",
            opacity=0.2,
            line_width=0,
            row=1,col=1)

    if zone == "DEMAND":
        fig.add_hrect(
            y0=df["l"].min(),
            y1=df["l"].min()*1.02,
            fillcolor="green",
            opacity=0.2,
            line_width=0,
            row=1,col=1)

    fig.add_trace(go.Bar(x=df["t"],y=df["v"],name="Volume"),
        row=2,col=1)

    fig.add_trace(go.Scatter(
        x=df["t"],y=df["rsi"],line=dict(color="purple"),name="RSI"),
        row=3,col=1)

    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False,
        title=symbol+" Technical Chart"
    )

    st.plotly_chart(fig,use_container_width=True)


# ================= SECTOR ROTATION MAP =================

def sector_rotation_map(df):

    st.subheader("📊 Sector Rotation Map")

    cols = st.columns(5)

    for i,row in df.iterrows():

        strength = row["Strength"]

        if strength >= 0.6:
            icon = "🟢"
        elif strength >= 0.3:
            icon = "🟡"
        else:
            icon = "🔴"

        with cols[i % 5]:
            st.markdown(f"""
### {row["Sector"]}

{icon} {strength}
""")


# ================= MARKET SCANNER =================

if mode == "F&O Market Scanner":

    if st.button("🚀 Scan Market"):

        st.subheader("Institutional Flow")

        flow = analyze_institutional_flow("NIFTY")

        col1,col2 = st.columns(2)

        with col1:
            st.markdown(f"""
<div class="metric-card">
PCR
<h2>{flow["PCR"]}</h2>
</div>
""", unsafe_allow_html=True)

        with col2:

            sentiment_class = "call" if flow["sentiment"]=="BULLISH" else "put"

            st.markdown(f"""
<div class="metric-card">
Market Sentiment
<h2 class="{sentiment_class}">{flow["sentiment"]}</h2>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")

        sector_data=[]

        for sector,stocks in sectors.items():

            strength=analyze_sector(smartApi,stocks)

            sector_data.append({
                "Sector":sector,
                "Strength":round(strength,2)
            })

        sector_df=pd.DataFrame(sector_data)
        sector_df=sector_df.sort_values(by="Strength",ascending=False)

        sector_rotation_map(sector_df)

        st.subheader("Sector Strength Ranking")
        st.dataframe(sector_df,use_container_width=True)

        st.subheader("Strong Sectors Today")
        st.dataframe(sector_df.head(2),use_container_width=True)

        st.markdown("---")

        st.subheader("All Trade Signals")

        results=run_scanner(smartApi)

        if not results:
            st.warning("No trade setup found.")
            st.stop()

        rows=[]

        for r in results:

            option=select_option(r["symbol"],r["direction"],r["spot"])

            row={
                "Stock":r["symbol"],
                "Direction":r["direction"],
                "Probability":str(r["probability"])+"%",
                "Volatility":r["volatility"],
                "Zone":r["smart_zone"],
                "Spot":round(r["spot"],2)
            }

            if option:
                row["Option"]=option["symbol"]
                row["Strike"]=option["strike"]
                row["Expiry"]=option["expiry"]
                row["Lot Size"]=option["lot_size"]
            else:
                row["Option"]="-"
                row["Strike"]="-"
                row["Expiry"]="-"
                row["Lot Size"]="-"

            rows.append(row)

        signals_df=pd.DataFrame(rows)

        st.dataframe(signals_df,use_container_width=True)

        st.markdown("---")

        st.subheader("Top 5 Trades")

        top5=signals_df.head(5)

        for i,row in top5.iterrows():

            direction_class = "call" if row["Direction"]=="CALL" else "put"

            st.markdown(f"""
### {row["Stock"]}

Direction: **<span class="{direction_class}">{row["Direction"]}</span>**

Probability: **{row["Probability"]}**

Volatility: **{row["Volatility"]}**

Smart Zone: **{row["Zone"]}**

Spot Price: **{row["Spot"]}**

Option: **{row["Option"]}**

Strike: **{row["Strike"]}**

Expiry: **{row["Expiry"]}**

Lot Size: **{row["Lot Size"]}**
""", unsafe_allow_html=True)

            prob=int(row["Probability"].replace("%",""))

            probability_gauge(prob)

            ai_trade_explanation(
                row["Direction"],
                row["Zone"],
                row["Volatility"]
            )

            indicator_chart(
                smartApi,
                row["Stock"],
                row["Zone"]
            )

            st.markdown("---")
