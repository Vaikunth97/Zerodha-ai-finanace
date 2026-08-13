from langchain_core.tools import tool

from Analytics.sector_analysis import compute_sector_breakdown


@tool
def sector_analysis_tool(portfolio_data: list[dict]) -> dict:
    """
    Analyze portfolio sector allocation using deterministic
    backend calculations.
    """

    import pandas as pd

    if not portfolio_data:
        return {
            "status": "unavailable",
            "message": "Portfolio data is not available."
        }

    df = pd.DataFrame(portfolio_data)

    breakdown = compute_sector_breakdown(df)

    clean_breakdown = {}

    for sector, data in breakdown.items():
        clean_breakdown[sector] = {
            "value": float(data["value"]),
            "percentage": float(data["pct_of_portfolio"]),
            "stock_count": int(data["stock_count"]),
        }

    return {
        "status": "success",
        "sector_breakdown": clean_breakdown,
    }