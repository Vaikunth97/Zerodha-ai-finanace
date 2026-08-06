"""
Analytics/benchmark_comparison.py
Compares the portfolio's performance against a market benchmark (default: Nifty 50).
Math only — takes the benchmark's day change % as input rather than fetching it
live, so this stays testable with dummy data.
"""
from Analytics.portfolio_analytics import compute_analytics

DEFAULT_BENCHMARK_SYMBOL = "^NSEI"  # Nifty 50 index


def compare_to_benchmark(df, benchmark_change_pct: float, benchmark_symbol: str = DEFAULT_BENCHMARK_SYMBOL) -> dict:
    analytics = compute_analytics(df)
    changes = [d["change_pct"] for d in analytics["raw_market_data"].values() if "change_pct" in d]
    portfolio_avg_change = round(sum(changes) / len(changes), 2) if changes else 0.0

    return {
        "benchmark_symbol": benchmark_symbol,
        "portfolio_avg_change_pct": portfolio_avg_change,
        "benchmark_change_pct": round(benchmark_change_pct, 2),
        "outperformance_pct": round(portfolio_avg_change - benchmark_change_pct, 2),
    }