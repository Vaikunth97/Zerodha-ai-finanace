from .client import ask_ai
def generate_portfolio_summary(portfolio_df):
    """
    Generate AI Portfolio Summary
    """

    prompt = f"""
You are an expert financial analyst.

Analyze the following stock portfolio.

Portfolio Data:

{portfolio_df.to_string(index=False)}

Generate the report in this format:


1. Portfolio Summary

2. Top Strengths

3. Possible Risks

4. Overall Suggestion

Keep the explanation simple.
"""

    return ask_ai(prompt)


if __name__ == "__main__":
    print(ask_ai("What is Artificial Intelligence?"))