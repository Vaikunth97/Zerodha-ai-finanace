from langchain_core.tools import tool
from Analytics.portfolio_analytics import calculate_portfolio_summary


@tool
def portfolio_summary_tool(portfolio_data: list[dict]) -> dict:
    """
    Calculate verified portfolio summary from backend analytics.

    Use this tool for overall portfolio:
    - value
    - investment
    - P&L
    - top holding
    - sector concentration
    - risk score
    """

    import pandas as pd

    if not portfolio_data:
        return {
            "status": "unavailable",
            "message": "Portfolio data is not available."
        }

    df = pd.DataFrame(portfolio_data)

    summary = calculate_portfolio_summary(df)

    return {
        "status": "success",
        "portfolio": {
            "total_value": float(summary.get("total_value", 0)),
            "total_investment": float(summary.get("total_investment", 0)),
            "profit_loss": float(summary.get("profit_loss", 0)),
            "profit_loss_pct": float(summary.get("profit_loss_pct", 0)),
            "top_holding": summary.get("top_holding"),
            "top_holding_pct": float(
                summary.get("top_holding_pct", 0)
            ),
            "risk_score": float(
                summary.get("risk_score", 0)
            ),
        }
    }