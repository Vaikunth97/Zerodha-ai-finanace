from .client import ask_ai


def portfolio_risk_analysis(portfolio_df):
    """
    Generate AI Portfolio Risk Analysis
    """

    prompt = f"""
You are an experienced financial risk analyst.

Analyze the following investment portfolio.

Portfolio:

{portfolio_df.to_string(index=False)}

Provide your analysis in this format:

1. Overall Risk Level

2. Main Risk Factors

3. Positive Factors

4. Risk Management Suggestions

5. Final Conclusion

Keep the response simple and beginner friendly.
try to complete the report in 650 token. If the report is too long, truncate it and provide a summary.
"""

    return ask_ai(prompt)