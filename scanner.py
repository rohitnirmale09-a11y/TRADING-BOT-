import sector_strength
from stock_engine import analyze_stock
from fo_scanner import get_fo_stocks
from concurrent.futures import ThreadPoolExecutor, as_completed
from sector_strength import get_strong_sectors
from institutional_flow import analyze_institutional_flow


def run_scanner(smartApi):

    print("\nChecking Institutional Flow...\n")

    flow = analyze_institutional_flow("NIFTY")
    market_bias = "NEUTRAL"

    if flow:
        print("PCR:", flow["PCR"])
        print("Market Sentiment:", flow["sentiment"])
        market_bias = flow["sentiment"]
    else:
        print("Institutional flow unavailable")

    # ===== SECTOR STRENGTH =====
    print("\nAnalyzing Sector Strength...\n")

    strong_sectors = get_strong_sectors(smartApi)

    print("Strong Sectors Today:\n")

    for sector in strong_sectors:
        print(sector[0], "Strength:", round(sector[1], 2))


    # ===== LOAD STOCKS =====
    print("\nLoading F&O stock list...\n")

    fo_stocks = get_fo_stocks()

    # ===== PRIORITIZE STRONG SECTOR STOCKS =====

    sector_stocks = []

    for sector in strong_sectors:
        sector_name = sector[0]

        if sector_name in sector_strength.sectors:
            sector_stocks.extend(sector_strength.sectors[sector_name])

    # remove duplicates
    sector_stocks = list(set(sector_stocks))

    # prioritize sector stocks
    fo_stocks = sector_stocks + [
        s for s in fo_stocks if s not in sector_stocks
    ]



    print("Scanning", len(fo_stocks), "F&O Stocks...\n")

    results = []


    # ===== MULTI THREAD SCANNER =====
    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = {
            executor.submit(analyze_stock, smartApi, stock): stock
            for stock in fo_stocks
        }

        for future in as_completed(futures):

            try:
                result = future.result()
            except:
                continue

            if not result:
                continue

            if result:

                if market_bias == "BULLISH" and result["direction"] == "CALL":
                    result["score"] += 1
            
                if market_bias == "BEARISH" and result["direction"] == "PUT":
                    result["score"] += 1


            print(
                result["symbol"],
                result["direction"],
                "   |  probability:",
                result["probability"],
                "   |   Volatility:",
                result.get("volatility", "UNKNOWN"),
                "   |   Zone:",
                result["smart_zone"]
            )

            results.append(result)


    if not results:
        return None


    # ===== SORT BY BEST SCORE =====
    results = sorted(results, key=lambda x: x["score"], reverse=True)


    # ===== RETURN TOP 5 =====
    return results[:5]