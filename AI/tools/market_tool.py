from langchain_core.tools import tool

from services.market import get_market_data, get_stock_info


@tool
def stock_market_tool(symbol: str) -> dict:
    """
    Fetch verified market information for an Indian stock.

    Use this tool for:
    - current price
    - previous close
    - daily change
    - daily change percentage
    - company information
    - sector
    - industry
    - market cap
    - P/E ratio
    - 52-week high
    - 52-week low
    - dividend yield
    """

    if not symbol or not symbol.strip():
        return {
            "status": "unavailable",
            "message": "Stock symbol is required."
        }

    symbol = symbol.strip().upper()

    try:
        market_data = get_market_data([symbol])
        stock_info = get_stock_info(symbol)

        current_data = market_data.get(symbol)

        if not current_data and not stock_info:
            return {
                "status": "unavailable",
                "symbol": symbol,
                "message": f"No market data is available for {symbol}."
            }

        return {
            "status": "success",
            "symbol": symbol,
            "market": {
                "current_price": (
                    float(current_data["current_price"])
                    if current_data
                    and current_data.get("current_price") is not None
                    else None
                ),
                "previous_close": (
                    float(current_data["Previous Close"])
                    if current_data
                    and current_data.get("Previous Close") is not None
                    else None
                ),
                "change": (
                    float(current_data["change"])
                    if current_data
                    and current_data.get("change") is not None
                    else None
                ),
                "change_pct": (
                    float(current_data["change_pct"])
                    if current_data
                    and current_data.get("change_pct") is not None
                    else None
                ),
            },
            "company": {
                "name": stock_info.get("Company name"),
                "sector": stock_info.get("sector"),
                "industry": stock_info.get("Industry"),
                "market_cap": stock_info.get("Market Cap"),
                "pe_ratio": stock_info.get("PE Ratio"),
                "52_week_high": stock_info.get("52 Week High"),
                "52_week_low": stock_info.get("52 Week Low"),
                "dividend_yield": stock_info.get("Dividend Yield"),
                "website": stock_info.get("Website"),
            },
        }

    except Exception:
        return {
            "status": "error",
            "symbol": symbol,
            "message": "Unable to fetch market data."
        }