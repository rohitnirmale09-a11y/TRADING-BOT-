import pandas as pd
import requests
from datetime import datetime

# ================= LOAD DATABASE ONCE =================

print("Loading option chain database...")

url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

data = requests.get(url).json()

master_df = pd.DataFrame(data)

# ================= LOAD OPTION CHAIN =================

def load_option_chain(symbol):

    df = master_df.copy()

    df = df[(df["name"] == symbol) & (df["instrumenttype"] == "OPTIDX")]

    if df.empty:
        return None

    df["expiry"] = pd.to_datetime(df["expiry"],format="mixed", errors="coerce")

    df = df.dropna(subset=["expiry"])

    nearest = df[df["expiry"] >= datetime.now()]["expiry"].min()

    df = df[df["expiry"] == nearest]

    return df


# ================= PCR CALCULATION =================

def calculate_pcr(df):

    calls = df[df["symbol"].str.endswith("CE")]
    puts = df[df["symbol"].str.endswith("PE")]

    call_count = len(calls)
    put_count = len(puts)

    if call_count == 0:
        return None

    pcr = put_count / call_count

    return round(pcr, 2)


# ================= INSTITUTIONAL SENTIMENT =================

def analyze_institutional_flow(symbol):

    df = load_option_chain(symbol)

    if df is None or len(df) == 0:
        return None

    pcr = calculate_pcr(df)

    sentiment = "NEUTRAL"

    if pcr is not None:

        if pcr > 1.2:
            sentiment = "BULLISH"

        elif pcr < 0.8:
            sentiment = "BEARISH"

    return {

        "PCR": pcr,
        "sentiment": sentiment

    }