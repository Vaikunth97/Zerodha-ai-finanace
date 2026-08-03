from .client import ask_ai


def ai_stock_recommendation(company_info):
    """
    Generate AI Buy/Hold/Sell recommendation.
    """

    prompt = f"""
You are an experienced stock market analyst.

Analyze the company information below.

Company Information:

{company_info}

Return your answer in this format:

Recommendation:
(Buy / Hold / Sell)

Reason:
- Point 1
- Point 2
- Point 3

Risk Level:
(Low / Medium / High)

Keep the answer simple.
"""

    return ask_ai(prompt)