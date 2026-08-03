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

Keep the answer under 250 words.
"""

    return ask_ai(prompt)