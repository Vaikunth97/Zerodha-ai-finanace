from .client import ask_ai


def explain_stock(company_info):
    """
    Generate AI explanation for a selected stock.
    """

    prompt = f"""
You are an expert stock market analyst.

Analyze the following company.

Company Information:

{company_info}

Generate the response in this format:

1. Company Overview

2. Strengths

3. Risks

4. Long-Term Outlook

Keep the explanation simple and beginner friendly.
"""

    return ask_ai(prompt)