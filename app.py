import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

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


# ================= TRADINGVIEW CHART =================

def tradingview_chart(symbol):

    html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>

      <script>
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 500,
        "symbol": "NSE:{symbol}",
        "interval": "5",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "toolbar_bg": "#1f2937",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """

    components.html(html, height=520)


# ================= F&O MARKET SCANNER =================

if mode == "F&O Market Scanner":

    if st.button("🚀 Scan Market"):

        # ===== INSTITUTIONAL FLOW =====

        st.subheader("Institutional Flow")

        flow = analyze_institutional_flow("NIFTY")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("PCR", flow["PCR"])

        with col2:
            st.metric("Market Sentiment", flow["sentiment"])

        st.markdown("---")


        # ===== SECTOR STRENGTH =====

        st.subheader("Sector Strength Ranking")

        sector_data = []

        for sector, stocks in sectors.items():

            strength = analyze_sector(smartApi, stocks)

            sector_data.append({
                "Sector": sector,
                "Strength": round(strength,2)
            })

        sector_df = pd.DataFrame(sector_data)

        sector_df = sector_df.sort_values(
            by="Strength",
            ascending=False
        )

        st.dataframe(sector_df, use_container_width=True)


        # ===== STRONG SECTORS =====

        st.subheader("Strong Sectors Today")

        strong = sector_df.head(2)

        st.dataframe(strong, use_container_width=True)

        st.markdown("---")


        # ===== SCAN STOCKS =====

        st.subheader("All Trade Signals")

        results = run_scanner(smartApi)

        if not results:
            st.warning("No trade setup found.")
            st.stop()

        rows = []

        for r in results:

            option = select_option(
                r["symbol"],
                r["direction"],
                r["spot"]
            )

            row = {
                "Stock": r["symbol"],
                "Direction": r["direction"],
                "Probability": str(r["probability"])+"%",
                "Volatility": r["volatility"],
                "Zone": r["smart_zone"],
                "Spot": round(r["spot"],2)
            }

            if option:

                row["Option"] = option["symbol"]
                row["Strike"] = option["strike"]
                row["Expiry"] = option["expiry"]
                row["Lot Size"] = option["lot_size"]

            else:

                row["Option"] = "-"
                row["Strike"] = "-"
                row["Expiry"] = "-"
                row["Lot Size"] = "-"

            rows.append(row)

        signals_df = pd.DataFrame(rows)

        st.dataframe(signals_df, use_container_width=True)

        st.markdown("---")


        # ===== TOP 5 TRADES =====

        st.subheader("Top 5 Trades")

        top5 = signals_df.head(5)

        for i,row in top5.iterrows():

            st.markdown(f"""
### {row["Stock"]}

Direction: **{row["Direction"]}**

Probability: **{row["Probability"]}**

Volatility: **{row["Volatility"]}**

Smart Zone: **{row["Zone"]}**

Spot Price: **{row["Spot"]}**

Option: **{row["Option"]}**

Strike: **{row["Strike"]}**

Expiry: **{row["Expiry"]}**

Lot Size: **{row["Lot Size"]}**
""")

            tradingview_chart(row["Stock"])

            st.markdown("---")


# ================= NIFTY ANALYSIS =================

elif mode == "NIFTY Analysis":

    if st.button("Analyze NIFTY"):

        result = analyze_index(smartApi,"NIFTY")

        if not result:
            st.warning("No setup found")
            st.stop()

        option = select_option(
            "NIFTY",
            result["direction"],
            result["spot"]
        )

        st.subheader("NIFTY Signal")

        st.metric("Direction", result["direction"])
        st.metric("Spot Price", round(result["spot"],2))

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        tradingview_chart("NIFTY")


# ================= BANKNIFTY ANALYSIS =================

elif mode == "BANKNIFTY Analysis":

    if st.button("Analyze BANKNIFTY"):

        result = analyze_index(smartApi,"BANKNIFTY")

        if not result:
            st.warning("No setup found")
            st.stop()

        option = select_option(
            "BANKNIFTY",
            result["direction"],
            result["spot"]
        )

        st.subheader("BANKNIFTY Signal")

        st.metric("Direction", result["direction"])
        st.metric("Spot Price", round(result["spot"],2))

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        tradingview_chart("BANKNIFTY")


# ================= CUSTOM STOCK =================

elif mode == "Custom Stock Analysis":

    symbol = st.text_input("Enter Stock Symbol (Example: SBIN)")

    if st.button("Analyze Stock"):

        if not symbol:
            st.warning("Enter stock symbol")
            st.stop()

        result = analyze_stock(
            smartApi,
            symbol.upper()
        )

        if not result:
            st.warning("No trade setup found")
            st.stop()

        option = select_option(
            result["symbol"],
            result["direction"],
            result["spot"]
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Direction", result["direction"])
            st.metric("Probability", str(result["probability"])+"%")

        with col2:
            st.metric("Volatility", result["volatility"])
            st.metric("Smart Zone", result["smart_zone"])

        st.metric("Spot Price", round(result["spot"],2))

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])

        tradingview_chart(symbol.upper())
