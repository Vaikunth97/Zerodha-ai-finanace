"""
Analytics/risk_alerts.py
Rule-based risk checks on top of the analytics engine's numbers. Math only.
"""
from Analytics.portfolio_analytics import compute_analytics

TOP_HOLDING_THRESHOLD_PCT = 25
SECTOR_CONCENTRATION_THRESHOLD_PCT = 40
DAY_DROP_THRESHOLD_PCT = -5


def get_risk_alerts(df) -> list:
    analytics = compute_analytics(df)
    alerts = []

    if analytics["top_holding_pct"] > TOP_HOLDING_THRESHOLD_PCT:
        alerts.append({
            "type": "concentration_risk",
            "severity": "high",
            "message": f"{analytics['top_holding']} is {analytics['top_holding_pct']}% of the portfolio, above {TOP_HOLDING_THRESHOLD_PCT}%.",
        })

    for sector, pct in analytics["sector_concentration_pct"].items():
        if pct > SECTOR_CONCENTRATION_THRESHOLD_PCT:
            alerts.append({
                "type": "sector_concentration_risk",
                "severity": "medium",
                "message": f"{sector} sector is {pct}% of the portfolio, above {SECTOR_CONCENTRATION_THRESHOLD_PCT}%.",
            })

    for symbol, data in analytics["raw_market_data"].items():
        change = data.get("change_pct")
        if change is not None and change <= DAY_DROP_THRESHOLD_PCT:
            alerts.append({
                "type": "volatility_alert",
                "severity": "medium",
                "message": f"{symbol} dropped {change}% today.",
            })

    return alerts