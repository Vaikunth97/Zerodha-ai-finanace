from .client import ask_ai


def portfolio_health_score(
    portfolio_df
):
    """
    Generate an AI-based portfolio health assessment.
    """

    if portfolio_df is None or portfolio_df.empty:

        return (
            "Portfolio data is unavailable."
        )

    portfolio_text = (
        portfolio_df.to_string(
            index=False
        )
    )

    prompt = f"""
Analyze the following investment portfolio.

PORTFOLIO:

{portfolio_text}

Generate a concise portfolio health assessment with:

1. Portfolio Health Score from 0 to 100
2. Reason for the score
3. Main strengths
4. Main weaknesses
5. Practical improvement suggestions

Base the analysis only on the portfolio information provided.

Do not invent market prices, company fundamentals,
future returns, or information that is not present
in the portfolio.

Keep the report concise.
"""

    return ask_ai(
        prompt
    )