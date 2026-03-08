import streamlit as st
import pandas as pd

from angel_login import angel_login
from scanner import run_scanner
from option_selector import select_option
from index_engine import analyze_index
from stock_engine import analyze_stock

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
    "Select Analysis Mode",
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
This engine scans:

• Institutional Flow  
• Sector Strength  
• Trend + RSI  
• Liquidity Sweep  
• Smart Money Zones  
• Volatility (ATR)
"""
)

# ================= F&O SCANNER =================

if mode == "F&O Market Scanner":

    st.subheader("📊 F&O Market Scanner")

    if st.button("🚀 Scan Market"):

        with st.spinner("Scanning F&O Stocks..."):

            results = run_scanner(smartApi)

        if not results:
            st.warning("No trade setup found.")
            st.stop()

        table = []

        for r in results:

            option = select_option(
                r["symbol"],
                r["direction"],
                r["spot"]
            )

            table.append({
                "Stock": r["symbol"],
                "Direction": r["direction"],
                "Probability": str(r["probability"])+"%",
                "Volatility": r["volatility"],
                "Smart Zone": r["smart_zone"],
                "Spot Price": round(r["spot"],2),
                "Option": option["symbol"] if option else "-"
            })

        df = pd.DataFrame(table)

        st.success("Top Trade Opportunities")

        st.dataframe(
            df,
            use_container_width=True
        )

# ================= NIFTY =================

elif mode == "NIFTY Analysis":

    st.subheader("📊 NIFTY Index Analysis")

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

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Direction", result["direction"])
            st.metric("Spot Price", round(result["spot"],2))

        with col2:
            if option:
                st.metric("Strike", option["strike"])
                st.metric("Option", option["symbol"])

# ================= BANKNIFTY =================

elif mode == "BANKNIFTY Analysis":

    st.subheader("📊 BANKNIFTY Index Analysis")

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

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Direction", result["direction"])
            st.metric("Spot Price", round(result["spot"],2))

        with col2:
            if option:
                st.metric("Strike", option["strike"])
                st.metric("Option", option["symbol"])

# ================= CUSTOM STOCK =================

elif mode == "Custom Stock Analysis":

    st.subheader("📊 Custom Stock Analysis")

    symbol = st.text_input("Enter Stock Symbol (Example: SBIN)")

    if st.button("Analyze Stock"):

        if not symbol:
            st.warning("Enter stock symbol")
            st.stop()

        result = analyze_stock(smartApi, symbol.upper())

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
            st.metric("Stock", result["symbol"])
            st.metric("Direction", result["direction"])
            st.metric("Probability", str(result["probability"])+"%")

        with col2:
            st.metric("Volatility", result["volatility"])
            st.metric("Smart Zone", result["smart_zone"])
            st.metric("Spot Price", round(result["spot"],2))

        st.markdown("---")

        if option:

            st.subheader("Suggested Option Trade")

            st.write("Option Symbol:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])
