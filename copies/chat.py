from .chat_chain import run_chat_chain


def portfolio_chat(
    portfolio_df,
    user_question,
    news_data=None
):
    """
    Compatibility wrapper for the existing FastAPI service.

    Converts the portfolio DataFrame into the format expected
    by the LangChain chat chain.
    """

    if portfolio_df is None or portfolio_df.empty:
        return "Portfolio data is not available."

    if not user_question or not user_question.strip():
        return "Please enter a finance-related question."

    try:
        # Convert DataFrame to list of dictionaries
        portfolio_data = portfolio_df.to_dict(
            orient="records"
        )

        # Send request to the new LangChain AI service
        return run_chat_chain(
            user_question=user_question,
            portfolio_data=portfolio_data
        )

    except Exception as e:
        return (
            "Unable to process your request at this time. "
            "Please try again."
        )