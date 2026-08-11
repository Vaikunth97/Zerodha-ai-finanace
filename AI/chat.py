from .client import ask_ai


def portfolio_chat(
    portfolio_df,
    user_question,
    news_data=None
):
    """
    AI Financial Advisor Chat

    Uses:
    1. Portfolio DataFrame
    2. User question
    3. Latest stock news from yfinance
    """

    # ========================================================
    # PORTFOLIO DATA
    # ========================================================

    portfolio_text = portfolio_df.to_string(
        index=False
    )


    # ========================================================
    # NEWS DATA
    # ========================================================

    news_text = ""

    if news_data:

        for stock, articles in news_data.items():

            news_text += f"\n\n===== {stock} =====\n"

            if not articles:

                news_text += (
                    "No recent news available.\n"
                )

                continue

            for article in articles[:5]:

                title = article.get(
                    "title",
                    ""
                )

                description = article.get(
                    "description",
                    ""
                )

                source = article.get(
                    "source",
                    ""
                )

                published = article.get(
                    "published",
                    ""
                )

                news_text += f"""
Title: {title}
Description: {description}
Source: {source}
Published: {published}
"""


    # ========================================================
    # AI PROMPT
    # ========================================================

    prompt = f"""
You are a professional financial portfolio advisor.

You are given the user's portfolio and the latest
available market news fetched using yfinance.

================ PORTFOLIO ================

{portfolio_text}


================ LATEST MARKET NEWS ================

{news_text}


================ USER QUESTION ================

{user_question}


================ INSTRUCTIONS ================

1. Answer the user's question using the portfolio data.

2. When the question is related to a particular stock,
   consider the latest available news for that stock.

3. Use the portfolio's current market data when available.

4. Do not invent prices, news, or financial information.

5. If relevant news is unavailable, clearly say so.

6. Explain the answer in simple English.

7. Keep the answer within approximately 650 tokens.

8. If the answer would become too long, summarize it.

9. Do not guarantee profits or future returns.

10. Clearly mention that the information is for
    educational purposes only and is not financial advice.
"""


    # ========================================================
    # SEND TO AI
    # ========================================================

    return ask_ai(prompt)
