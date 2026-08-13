from langchain_core.tools import tool

from Analytics.portfolio_analytics import (
    calculate_total_investment,
    calculate_current_value,
    calculate_profit_loss,
    calculate_profit_loss_percentage,
    get_top_gainers,
    get_top_losers,
)


@tool
def portfolio_performance_tool(portfolio_data: list[dict]) -> dict:
    """
    Analyze portfolio performance using deterministic backend calculations.

    Use this tool for:
    - total investment
    - current portfolio value
    - profit/loss
    - profit/loss percentage
    - top gainers
    - top losers
    """

    import pandas as pd

    if not portfolio_data:
        return {
            "status": "unavailable",
            "message": "Portfolio data is not available."
        }

    df = pd.DataFrame(portfolio_data)

    total_investment = calculate_total_investment(df)
    current_value = calculate_current_value(df)
    profit_loss = calculate_profit_loss(df)
    profit_loss_percentage = calculate_profit_loss_percentage(df)

    top_gainers = get_top_gainers(df)
    top_losers = get_top_losers(df)

    return {
        "status": "success",
        "performance": {
            "total_investment": float(total_investment),
            "current_value": float(current_value),
            "profit_loss": float(profit_loss),
            "profit_loss_percentage": float(profit_loss_percentage),
        },
        "top_gainers": [
            {
                "symbol": item["symbol"],
                "change_pct": float(item["change_pct"]),
            }
            for item in top_gainers
        ],
        "top_losers": [
            {
                "symbol": item["symbol"],
                "change_pct": float(item["change_pct"]),
            }
            for item in top_losers
        ],
    }