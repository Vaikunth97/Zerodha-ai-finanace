"""
Analytics/portfolio_analytics.py
The ANALYTICS ENGINE — computes deterministic numbers from the portfolio
DataFrame only. No AI calls, no live market calls here (golden rule).

Expects a DataFrame with these columns (matches the dummy dataset):
Stock Symbol, Quantity, Average Price, Current Price, Sector, Daily Change %
"""


def compute_analytics(df) -> dict:
    if df is None or df.empty:
        return {
            "total_value": 0.0,
            "sector_concentration_pct": {},
            "top_holding": None,
            "top_holding_pct": 0.0,
            "raw_market_data": {},
        }

    holdings = df.to_dict("records")

    total_value = 0.0
    sector_value: dict = {}
    stock_values: dict = {}
    raw_market_data: dict = {}

    for h in holdings:
        symbol = h["Stock Symbol"]
        price = h.get("Current Price") or h["Average Price"]
        value = price * h["Quantity"]

        total_value += value
        stock_values[symbol] = value

        sector = h.get("Sector", "Unknown")
        sector_value[sector] = sector_value.get(sector, 0) + value

        raw_market_data[symbol] = {
            "current_price": round(price, 2),
            "change_pct": h.get("Daily Change %", 0.0),
        }

    concentration = {
        sector: round(val / total_value * 100, 2) for sector, val in sector_value.items()
    }
    top_holding = max(stock_values, key=stock_values.get)

    return {
        "total_value": round(total_value, 2),
        "sector_concentration_pct": concentration,
        "top_holding": top_holding,
        "top_holding_pct": round(stock_values[top_holding] / total_value * 100, 2),
        "raw_market_data": raw_market_data,
    }


def calculate_total_investment(df) -> float:
    """Total amount invested at average buy price (not current value)."""
    return round((df["Average Price"] * df["Quantity"]).sum(), 2)


def calculate_current_value(df) -> float:
    """Total portfolio value at current market prices."""
    price = df["Current Price"].fillna(df["Average Price"])
    return round((price * df["Quantity"]).sum(), 2)


def calculate_profit_loss(df) -> float:
    """Absolute profit/loss: current value minus invested amount."""
    return round(calculate_current_value(df) - calculate_total_investment(df), 2)


def calculate_profit_loss_percentage(df) -> float:
    """Profit/loss as a percentage of the invested amount."""
    invested = calculate_total_investment(df)
    if invested == 0:
        return 0.0
    return round(calculate_profit_loss(df) / invested * 100, 2)


def get_top_gainers(df, limit: int = 3) -> list:
    """Top N stocks by highest daily change %, sorted descending."""
    ranked = df.sort_values("change_pct", ascending=False).head(limit)
    return [
        {"symbol": row["Stock Symbol"], "change_pct": row["change_pct"]}
        for _, row in ranked.iterrows()
    ]


def get_top_losers(df, limit: int = 3) -> list:
    """Top N stocks by lowest (most negative) daily change %, sorted ascending."""
    ranked = df.sort_values("change_pct", ascending=True).head(limit)
    return [
        {"symbol": row["Stock Symbol"], "change_pct": row["change_pct"]}
        for _, row in ranked.iterrows()
    ]


TOP_HOLDING_RISK_WEIGHT = 4
SECTOR_CONCENTRATION_RISK_WEIGHT = 3
VOLATILITY_RISK_WEIGHT = 3


def calculate_risk_score(analytics: dict) -> float:
    """Single risk score 0 (low) to 10 (high): concentration + sector + volatility."""
    score = 0.0

    top_pct = analytics.get("top_holding_pct", 0)
    if top_pct > 25:
        score += min((top_pct - 25) / 75 * TOP_HOLDING_RISK_WEIGHT, TOP_HOLDING_RISK_WEIGHT)

    max_sector_pct = max(analytics.get("sector_concentration_pct", {}).values(), default=0)
    if max_sector_pct > 40:
        score += min((max_sector_pct - 40) / 60 * SECTOR_CONCENTRATION_RISK_WEIGHT, SECTOR_CONCENTRATION_RISK_WEIGHT)

    changes = [abs(d.get("change_pct", 0)) for d in analytics.get("raw_market_data", {}).values()]
    avg_volatility = sum(changes) / len(changes) if changes else 0
    score += min(avg_volatility / 5 * VOLATILITY_RISK_WEIGHT, VOLATILITY_RISK_WEIGHT)

    return round(min(score, 10.0), 1)


def calculate_portfolio_summary(df) -> dict:
    """Complete portfolio picture: base analytics + investment, P&L, movers, risk score."""
    base_analytics = compute_analytics(df)

    if df is None or df.empty:
        return {**base_analytics, "total_investment": 0.0, "profit_loss": 0.0,
                "profit_loss_pct": 0.0, "top_gainers": [], "top_losers": [], "risk_score": 0.0}

    return {
        **base_analytics,
        "total_investment": calculate_total_investment(df),
        "profit_loss": calculate_profit_loss(df),
        "profit_loss_pct": calculate_profit_loss_percentage(df),
        "top_gainers": get_top_gainers(df),
        "top_losers": get_top_losers(df),
        "risk_score": calculate_risk_score(base_analytics),
    }
