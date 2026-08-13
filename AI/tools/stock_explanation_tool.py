from langchain_core.tools import tool

from .market_tool import stock_market_tool
from .news_tool import stock_news_tool
from .performance_tool import portfolio_performance_tool


@tool
def stock_explanation_tool(
    symbol: str,
    portfolio_data: list[dict] | None = None
) -> dict:
    """
    Combine verified market data, recent news, and portfolio
    impact for a stock.
    """

    if not symbol or not symbol.strip():
        return {
            "status": "unavailable",
            "message": "Stock symbol is required."
        }

    symbol = symbol.strip().upper()

    # Market data
    market_result = stock_market_tool.invoke({
        "symbol": symbol
    })

    # Recent news
    news_result = stock_news_tool.invoke({
        "symbol": symbol
    })

    # Portfolio impact
    portfolio_result = None

    if portfolio_data:
        portfolio_result = portfolio_performance_tool.invoke({
            "portfolio_data": portfolio_data
        })

    return {
        "status": "success",
        "symbol": symbol,
        "market": market_result,
        "news": news_result,
        "portfolio_impact": portfolio_result,
    }