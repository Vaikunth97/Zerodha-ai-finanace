from .client import ask_ai
def portfolio_chat(portfolio_df, user_question):
    """
    AI Financial Advisor Chat
    """

    prompt = f"""
You are a professional financial advisor.

Portfolio:

{portfolio_df.to_string(index=False)}

User Question:

{user_question}

Answer in simple English.

Do not guarantee profits.

Mention that this is for educational purposes only.
"""

    return ask_ai(prompt)