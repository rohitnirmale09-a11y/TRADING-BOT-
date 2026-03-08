import pandas as pd
import requests


def get_fo_stocks():

    print("Loading F&O stock list...")

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    # Only stock options
    df = df[df["instrumenttype"] == "OPTSTK"]

    # Remove duplicates
    fo_stocks = df["name"].unique().tolist()

    return fo_stocks