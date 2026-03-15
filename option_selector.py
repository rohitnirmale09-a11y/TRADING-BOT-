import pandas as pd
import requests
from datetime import datetime

def select_option(symbol, direction, spot):

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    # FILTER INDEX OR STOCK
    if symbol in ["NIFTY", "BANKNIFTY"]:
        df = df[df["instrumenttype"] == "OPTIDX"]
    else:
        df = df[df["instrumenttype"] == "OPTSTK"]

    df = df[df["name"] == symbol]

    if df.empty:
        return None

    # expiry
    df["expiry"] = pd.to_datetime(df["expiry"], format="mixed", errors="coerce")
    df = df.dropna(subset=["expiry"])

    # ===== CHOOSE NEXT WEEK EXPIRY =====
    expiries = sorted(df[df["expiry"] >= datetime.now()]["expiry"].unique())

    if len(expiries) > 1:
        chosen_expiry = expiries[1]   # next week expiry
    else:
        chosen_expiry = expiries[0]   # fallback if only one expiry

    df = df[df["expiry"] == chosen_expiry]

    # strike
    df["strike"] = pd.to_numeric(df["strike"], errors="coerce") / 100

    option_type = "CE" if direction == "CALL" else "PE"

    df = df[df["symbol"].str.endswith(option_type)]

    if df.empty:
        return None

    # ===== FIND ATM STRIKE =====
    df["distance"] = abs(df["strike"] - spot)

    atm = df.sort_values("distance").iloc[0]

    return {
        "symbol": atm["symbol"],
        "strike": atm["strike"],
        "expiry": atm["expiry"].date(),
        "lot_size": atm["lotsize"]
    }