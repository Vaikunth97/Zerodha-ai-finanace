from .client import ask_ai


def portfolio_health_score(portfolio_df):
    """
    Generate AI Portfolio Health Score
    """

    prompt = f"""
You are an expert financial advisor.

Analyze the following investment portfolio.

Portfolio:

{portfolio_df.to_string(index=False)}

Generate:

1. Portfolio Health Score (0-100)

2. Reason for the Score

3. Strengths

4. Weaknesses

5. Suggestions to Improve Score


try to keep token 650 in mind while generating the report. If the report is too long, truncate it and provide a summary.
"""

    return ask_ai(prompt)