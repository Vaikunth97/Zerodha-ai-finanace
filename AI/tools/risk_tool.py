from langchain_core.tools import tool

from Analytics.risk_alerts import get_risk_alerts
from Analytics.portfolio_analytics import calculate_portfolio_summary


@tool
def risk_analysis_tool(portfolio_data: list[dict]) -> dict:
    """
    Analyze portfolio risk using deterministic backend analytics.

    Use this tool when the user asks about:
    - risk score
    - concentration risk
    - sector risk
    - volatility alerts
    - portfolio risk warnings
    """

    import pandas as pd

    if not portfolio_data:
        return {
            "status": "unavailable",
            "message": "Portfolio data is not available."
        }

    df = pd.DataFrame(portfolio_data)

    summary = calculate_portfolio_summary(df)
    alerts = get_risk_alerts(df)

    return {
        "status": "success",
        "risk": {
            "risk_score": float(summary.get("risk_score", 0)),
            "top_holding": summary.get("top_holding"),
            "top_holding_pct": float(
                summary.get("top_holding_pct", 0)
            ),
        },
        "risk_alerts": alerts,
    }