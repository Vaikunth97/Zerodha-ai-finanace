"""
Analytics/sector_analysis.py
Deterministic sector-wise breakdown of the portfolio. Math only.
"""


def compute_sector_breakdown(df) -> dict:
    if df is None or df.empty:
        return {}

    price = df["Current Price"].fillna(df["Average Price"])
    value = price * df["Quantity"]
    total_value = value.sum()

    breakdown = {}
    for sector in df["Sector"].unique():
        mask = df["Sector"] == sector
        sector_value = value[mask].sum()
        breakdown[sector] = {
            "value": round(sector_value, 2),
            "pct_of_portfolio": round(sector_value / total_value * 100, 2) if total_value else 0.0,
            "stock_count": int(mask.sum()),
        }
    return breakdown