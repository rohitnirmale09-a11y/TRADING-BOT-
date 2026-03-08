import streamlit as st
import pandas as pd

from angel_login import angel_login
from scanner import run_scanner
from sector_strength import get_strong_sectors
from institutional_flow import analyze_institutional_flow
from option_selector import select_option
from index_engine import analyze_index
from stock_engine import analyze_stock


# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="AI Swing Option Engine",
    page_icon="📈",
    layout="wide"
)

# ================= CUSTOM CSS =================

st.markdown("""
<style>

.main-title{
font-size:36px;
font-weight:bold;
color:#1f77b4;
}

.section-title{
font-size:24px;
font-weight:bold;
margin-top:20px;
}

.card{
padding:15px;
border-radius:10px;
background-color:#f7f7f7;
margin-bottom:10px;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📈 AI Swing Option Trading Dashboard</div>', unsafe_allow_html=True)
st.caption("Institutional Style Market Scanner")


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
Engine Uses:

• Institutional Flow  
• Sector Strength  
• Trend + RSI  
• Liquidity Sweep  
• Smart Money Zones  
• ATR Volatility  
"""
)

# ================= F&O SCANNER =================

if mode == "F&O Market Scanner":

    st.markdown('<div class="section-title">📊 Market Scanner</div>', unsafe_allow_html=True)

    if st.button("🚀 Scan Market"):

        # ================= INSTITUTIONAL FLOW =================

        flow = analyze_institutional_flow("NIFTY")

        st.markdown('<div class="section-title">Institutional Flow</div>', unsafe_allow_html=True)

        c1,c2 = st.columns(2)

        with c1:
            st.metric("PCR", flow["PCR"])

        with c2:
            st.metric("Market Sentiment", flow["sentiment"])


        # ================= SECTOR STRENGTH =================

        st.markdown('<div class="section-title">Sector Strength Ranking</div>', unsafe_allow_html=True)

        sectors = get_strong_sectors(smartApi)

        sector_data = []

        for s in sectors:
            sector_data.append({
                "Sector": s[0],
                "Strength": round(s[1],2)
            })

        df_sector = pd.DataFrame(sector_data)

        st.dataframe(df_sector, use_container_width=True)


        # ================= TOP 2 SECTORS =================

        st.markdown('<div class="section-title">Strong Sectors Today</div>', unsafe_allow_html=True)

        st.dataframe(df_sector.head(2), use_container_width=True)


        # ================= RUN SCANNER =================

        with st.spinner("Scanning F&O Stocks..."):

            results = run_scanner(smartApi)

        if not results:
            st.warning("No trade setups found")
            st.stop()


        # ================= ALL SIGNALS =================

        st.markdown('<div class="section-title">All Trade Signals</div>', unsafe_allow_html=True)

        table = []

        for r in results:

            option = select_option(
                r["symbol"],
                r["direction"],
                r["spot"]
            )

            if option:

                strike = option["strike"]
                expiry = option["expiry"]
                lot = option["lot_size"]
                option_symbol = option["symbol"]

            else:

                strike = "-"
                expiry = "-"
                lot = "-"
                option_symbol = "-"

            table.append({

                "Stock": r["symbol"],
                "Direction": r["direction"],
                "Probability": str(r["probability"])+"%",
                "Volatility": r["volatility"],
                "Zone": r["smart_zone"],
                "Spot": round(r["spot"],2),
                "Option": option_symbol,
                "Strike": strike,
                "Expiry": expiry,
                "Lot Size": lot
            })

        df = pd.DataFrame(table)

        st.dataframe(df, use_container_width=True)


        # ================= TOP 5 =================

        st.markdown('<div class="section-title">Top 5 Trades</div>', unsafe_allow_html=True)

        top5 = df.head(5)

        for i,row in top5.iterrows():

            st.markdown(f"""
            <div class="card">

            <b>{row["Stock"]}</b><br>

            Direction: {row["Direction"]} <br>
            Probability: {row["Probability"]} <br>
            Volatility: {row["Volatility"]} <br>
            Zone: {row["Zone"]} <br>

            Spot: {row["Spot"]} <br>

            Option: {row["Option"]} <br>
            Strike: {row["Strike"]} <br>
            Expiry: {row["Expiry"]} <br>
            Lot Size: {row["Lot Size"]}

            </div>
            """, unsafe_allow_html=True)


# ================= INDEX ANALYSIS =================

elif mode == "NIFTY Analysis":

    st.subheader("NIFTY Analysis")

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

        st.metric("Direction", result["direction"])
        st.metric("Spot", round(result["spot"],2))

        if option:

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])


elif mode == "BANKNIFTY Analysis":

    st.subheader("BANKNIFTY Analysis")

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

        st.metric("Direction", result["direction"])
        st.metric("Spot", round(result["spot"],2))

        if option:

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])


# ================= CUSTOM STOCK =================

elif mode == "Custom Stock Analysis":

    st.subheader("Custom Stock")

    symbol = st.text_input("Enter Stock Symbol")

    if st.button("Analyze"):

        result = analyze_stock(smartApi, symbol.upper())

        if not result:
            st.warning("No setup found")
            st.stop()

        option = select_option(
            result["symbol"],
            result["direction"],
            result["spot"]
        )

        st.metric("Direction", result["direction"])
        st.metric("Probability", str(result["probability"])+"%")

        st.metric("Volatility", result["volatility"])
        st.metric("Smart Zone", result["smart_zone"])

        st.write("Spot:", round(result["spot"],2))

        if option:

            st.write("Option:", option["symbol"])
            st.write("Strike:", option["strike"])
            st.write("Expiry:", option["expiry"])
            st.write("Lot Size:", option["lot_size"])
