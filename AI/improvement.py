from .client import ask_ai


def portfolio_improvement_suggestions(portfolio_df):
    """
    Generate AI suggestions to improve portfolio.
    """

    prompt = f"""
You are an experienced financial advisor.

Analyze the portfolio below.

Portfolio:

{portfolio_df.to_string(index=False)}

Provide:

1. Portfolio Strengths

2. Weaknesses

3. Diversification Suggestions

4. Risk Reduction Tips

5. Final Advice

Keep the response beginner friendly.
try to complete the report in 650 tokens. If the report is too long, truncate it and provide a summary.
"""

    return ask_ai(prompt)