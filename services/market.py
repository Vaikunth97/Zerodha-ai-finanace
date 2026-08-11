import yfinance as yf
import pandas as pd
#taking data from the portfolios
def get_market_data(symbols):
    market_data = {}
    for symbol in symbols:


        try:
            stock = yf.Ticker(f"{symbol}.NS")
            history = stock.history(period = "2d") #give latest price of two day ago
            if history.empty:
                continue
            current_price = round(history["Close"].iloc[-1],2) #give last data
            
            if len(history) > 1:
                previous_close = round(history["Close"].iloc[-2],2)
            else:
                previous_close = current_price
            change = round(current_price - previous_close,2)

            if previous_close != 0:
                change_pct = round((change/previous_close) * 100,2)
            else:
                change_pct = 0

            market_data[symbol] = {
                "current_price": current_price,
                "previous_close": previous_close,
                "change": change,
                "change_pct": change_pct
            }
        except Exception as e:
            print(f"Error fectching{symbol}:{e}")
    return market_data
            


def updated_current_price(df):
    symbols = df["Stock Symbol"].tolist()
    market_data = get_market_data(symbols)

    current_price = []
    previous_close = []
    change = []
    change_pct = []

    for symbol in symbols:
        data = market_data.get(symbol,{})
        current_price.append(data.get("current_price"))
        previous_close.append(data.get("previous_close"))
        change.append(data.get("change"))
        change_pct.append(data.get("change_pct"))
    df["Current Price"] = current_price
    df["Previous Close"] = previous_close
    df["Change"] = change
    df["Change %"] = change_pct
    return df


def get_stock_info(symbol):
    try:
        stock = yf.Ticker(f"{symbol}.NS")
        info = stock.info
        return {"Company name": info.get("longName"),
                "Current Price": info.get("currentPrice"),
                "sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Market Cap": info.get("marketCap"),
                "PE Ratio": info.get("trailingPE"),
                "52 Week High": info.get("fiftyTwoWeekHigh"),
                "52 Week Low": info.get("fiftyTwoWeekLow"),
                "Dividend Yield": info.get("dividendYield"),
                "Website": info.get("website")}

    except Exception as e:
        print(f"Error feching data for {symbol} : {e}")
        return {}
