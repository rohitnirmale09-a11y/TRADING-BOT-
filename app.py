import streamlit as st
import pandas as pd

from angel_login import angel_login
from scanner import run_scanner
from sector_strength import get_strong_sectors
from institutional_flow import analyze_institutional_flow
from option_selector import select_option

# ================= PAGE =================

st.set_page_config(
    page_title="AI Swing Option Engine",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Swing Option Trading Dashboard")
st.caption("Institutional Style Swing Scanner")

# ================= LOGIN =================

@st.cache_resource
def login():
    return angel_login()

smartApi = login()

# ================= BUTTON =================

if st.button("🚀 Scan Market"):

    # ================= INSTITUTIONAL FLOW =================

    st.subheader("Institutional Flow")

    flow = analyze_institutional_flow("NIFTY")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("PCR", flow["PCR"])

    with col2:
        st.metric("Market Sentiment", flow["sentiment"])

    # ================= SECTOR STRENGTH =================

    st.subheader("Sector Strength")

    sectors = get_strong_sectors(smartApi)

    sector_table = []

    for s in sectors:
        sector_table.append({
            "Sector": s[0],
            "Strength": round(s[1],2)
        })

    st.dataframe(pd.DataFrame(sector_table), use_container_width=True)

    # ================= RUN SCANNER =================

    st.subheader("Scanning F&O Stocks")

    results = run_scanner(smartApi)

    if not results:
        st.warning("No setup found")
        st.stop()

    # ================= ALL SCANNED STOCKS =================

    st.subheader("All Trade Signals")

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

    st.subheader("Top 5 Trades")

    top5 = df.head(5)

    for i, row in top5.iterrows():

        st.markdown("### "+row["Stock"])

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Direction", row["Direction"])

        with c2:
            st.metric("Probability", row["Probability"])

        with c3:
            st.metric("Volatility", row["Volatility"])

        with c4:
            st.metric("Zone", row["Zone"])

        st.write("Spot:", row["Spot"])
        st.write("Option:", row["Option"])
        st.write("Strike:", row["Strike"])
        st.write("Expiry:", row["Expiry"])
        st.write("Lot Size:", row["Lot Size"])

        st.markdown("---")
