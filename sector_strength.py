from stock_engine import analyze_stock


sectors = {

    "BANKING": [
        "HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"
    ],

    "IT": [
        "TCS","INFY","HCLTECH","WIPRO","TECHM"
    ],

    "AUTO": [
        "TATAMOTORS","M&M","MARUTI","HEROMOTOCO","BAJAJ-AUTO"
    ],

    "METAL": [
        "TATASTEEL","JSWSTEEL","HINDALCO","VEDL","JINDALSTEL"
    ],

    "PHARMA": [
        "SUNPHARMA","CIPLA","DRREDDY","DIVISLAB","LUPIN"
    ],

    "FMCG": [
        "HINDUNILVR","ITC","NESTLEIND","BRITANNIA","TATACONSUM"
    ],

    "ENERGY": [
        "RELIANCE","ONGC","IOC","BPCL","GAIL"
    ],

    "INFRA": [
        "LT","NBCC","IRB","KEC","ADANIENT"
    ],

    "FINANCE": [
        "BAJFINANCE","BAJAJFINSV","LICHSGFIN","CHOLAFIN","SHRIRAMFIN"
    ],

    "REALTY": [
        "DLF","LODHA","GODREJPROP","OBEROIRLTY","BRIGADE"
    ],

    "DEFENCE": [
        "HAL","BEL","BDL","MAZDOCK","COCHINSHIP"
    ],

    "PSU": [
        "NTPC","POWERGRID","COALINDIA"
    ],

    "TELECOM": [
        "BHARTIARTL","IDEA"
    ],

    "CHEMICAL": [
        "PIIND","UPL","SRF","DEEPAKNTR"
    ],

    "CAPITAL_GOODS": [
        "SIEMENS","ABB","CUMMINSIND","THERMAX"
    ]

}


def analyze_sector(smartApi, stocks):

    score = 0
    valid = 0

    for symbol in stocks:

        result = analyze_stock(smartApi, symbol)

        if not result:
            continue

        valid += 1

        if result["direction"] == "CALL":
            score += 1


    if valid == 0:
        return 0


    return score / valid



def get_strong_sectors(smartApi):

    print("\nAnalyzing Sector Strength...\n")

    results = []

    for sector, stocks in sectors.items():

        strength = analyze_sector(smartApi, stocks)

        results.append((sector, strength))


    results = sorted(results, key=lambda x: x[1], reverse=True)


    print("\nSector Strength Ranking:\n")

    for sector, strength in results:
        print(sector, "Strength:", round(strength,2))


    return results[:2]