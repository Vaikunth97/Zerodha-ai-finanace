import os
import streamlit as st
from openai import OpenAI

api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is not configured.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        if not response.choices:
            return "❌ AI did not return any response."

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {e}"


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
"""

    return ask_ai(prompt)
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
"""

    return ask_ai(prompt)
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