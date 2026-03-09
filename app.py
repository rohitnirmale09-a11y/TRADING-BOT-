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

st.markdown("""
<style>

.stApp {
background-color:#0f172a;
}

/* Text */
html, body {
color:white;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
color:white !important;
}

/* Paragraph */
p {
color:#e5e7eb !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
color:white !important;
font-size:28px !important;
}

[data-testid="stMetricLabel"] {
color:#cbd5e1 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
background-color:#111827;
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


# ================= SECTOR CACHE =================

@st.cache_data(ttl=600)
def get_sector_strength(api):

    sector_data = []

    for sector, stocks in sectors.items():

        strength = analyze_sector(api, stocks)

        sector_data.append({
            "Sector": sector,
            "Strength": round(strength,2)
        })

    df = pd.DataFrame(sector_data)

    return df.sort_values(by="Strength", ascending=False)


# ================= INDICATOR CHART =================

def indicator_chart(smartApi, symbol, zone):

    search = smartApi.searchScrip("NSE", symbol)

    if "data" not in search or len(search["data"]) == 0:
        st.warning("Symbol not found")
        return

    token = None

    for item in search["data"]:
        if item["tradingsymbol"].endswith("-EQ"):
            token = item["symboltoken"]
            break

    if not token:
        st.warning("Token not found")
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
            st.metric("PCR", flow["PCR"])

        with col2:
            st.metric("Market Sentiment", flow["sentiment"])

        st.markdown("---")

        sector_df = get_sector_strength(smartApi)

        sector_rotation_map(sector_df)

        st.subheader("Sector Strength Ranking")
        st.dataframe(sector_df,use_container_width=True)

        st.subheader("Strong Sectors Today")
        st.dataframe(sector_df.head(2),use_container_width=True)

        st.markdown("---")

        st.subheader("All Trade Signals")

        results = run_scanner(smartApi)

        if not results:
            st.warning("NO TRADE SETUP FOUND.")
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

            rows.append(row)

        signals_df=pd.DataFrame(rows)
        if signals_df.empty:
            st.warning("NO VALID TRADE FOUND.")
            st.stop()
        

        st.dataframe(signals_df,use_container_width=True)

        st.markdown("---")

        st.subheader("Top 5 Trades")

        for i,row in signals_df.head(5).iterrows():
        
            st.markdown(f"""
            ### {row["Stock"]}
        
            Direction: **{row["Direction"]}**
        
            Probability: **{row["Probability"]}**
        
            Volatility: **{row["Volatility"]}**
        
            Smart Zone: **{row["Zone"]}**
            """)
        
            # OPTION DETAILS
            if "Option" in row and row["Option"] != "-":
                st.write("Option:", row["Option"])
                st.write("Strike:", row["Strike"])
                st.write("Expiry:", row["Expiry"])
                st.write("Lot Size:", row["Lot Size"])
        
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
# ================= NIFTY ANALYSIS =================

elif mode == "NIFTY Analysis":

    if st.button("Analyze NIFTY"):

        st.subheader("Institutional Flow")

        flow = analyze_institutional_flow("NIFTY")

        col1,col2 = st.columns(2)

        with col1:
            st.metric("PCR", flow["PCR"])

        with col2:
            st.metric("Market Sentiment", flow["sentiment"])

        st.markdown("---")

        # Sector Strength
        

        st.markdown("---")

        # Index Signal

        result = analyze_index(smartApi,"NIFTY")
        if not result:
            st.warning("NO NIFTY SETUP FOUND.")
            st.stop()

        option = select_option(
            "NIFTY",
            result["direction"],
            result["spot"]
        )

        direction_class = "call" if result["direction"]=="CALL" else "put"

        st.markdown(f"""
### NIFTY SIGNAL

Direction: **<span class="{direction_class}">{result["direction"]}</span>**

Spot Price: **{round(result["spot"],2)}**
""", unsafe_allow_html=True)

        prob = 60
        probability_gauge(prob)

        ai_trade_explanation(
            result["direction"],
            "NONE",
            "MEDIUM"
        )

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        indicator_chart(
            smartApi,
            "NIFTY",
            "NONE"
        )


# ================= BANKNIFTY ANALYSIS =================

elif mode == "BANKNIFTY Analysis":

    if st.button("Analyze BANKNIFTY"):

        st.subheader("Institutional Flow")

        flow = analyze_institutional_flow("BANKNIFTY")

        col1,col2 = st.columns(2)

        with col1:
            st.metric("PCR", flow["PCR"])

        with col2:
            st.metric("Market Sentiment", flow["sentiment"])

        st.markdown("---")

        

        st.markdown("---")

        result = analyze_index(smartApi,"BANKNIFTY")
        if not result:
            st.warning("NO NIFTY SETUP FOUND.")
            st.stop()

        option = select_option(
            "BANKNIFTY",
            result["direction"],
            result["spot"]
        )

        direction_class = "call" if result["direction"]=="CALL" else "put"

        st.markdown(f"""
### BANKNIFTY SIGNAL

Direction: **<span class="{direction_class}">{result["direction"]}</span>**

Spot Price: **{round(result["spot"],2)}**
""", unsafe_allow_html=True)

        prob = 60
        probability_gauge(prob)

        ai_trade_explanation(
            result["direction"],
            "NONE",
            "MEDIUM"
        )

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        indicator_chart(
            smartApi,
            "BANKNIFTY",
            "NONE"
        )


# ================= CUSTOM STOCK =================

elif mode == "Custom Stock Analysis":

    symbol = st.text_input("Enter Stock Symbol (Example: SBIN)")

    if st.button("Analyze Stock"):

        if not symbol:
            st.warning("Please enter a stock symbol.")
            st.stop()

        result = analyze_stock(
            smartApi,
            symbol.upper()
        )

        if not result:
            st.warning("No trade setup")
            st.stop()

        option = select_option(
            result["symbol"],
            result["direction"],
            result["spot"]
        )

        direction_class = "call" if result["direction"]=="CALL" else "put"

        st.markdown(f"""
### {result["symbol"]}

Direction: **<span class="{direction_class}">{result["direction"]}</span>**

Probability: **{result["probability"]}%**

Volatility: **{result["volatility"]}**

Smart Zone: **{result["smart_zone"]}**

Spot Price: **{round(result["spot"],2)}**
""", unsafe_allow_html=True)

        probability_gauge(result["probability"])

        ai_trade_explanation(
            result["direction"],
            result["smart_zone"],
            result["volatility"]
        )

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        indicator_chart(
            smartApi,
            symbol.upper(),
            result["smart_zone"]
        )
