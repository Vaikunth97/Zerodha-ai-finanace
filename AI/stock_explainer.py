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
try to complete the report in 650 token. If the report is too long, truncate it and provide a summary.
"""

    return ask_ai(prompt)