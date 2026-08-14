# ============================================================
# ZERODHA AI - HYBRID CHAT CHAIN
# Portfolio + RAG + Tools + News
# ============================================================

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from .memory import ChatMemory

from .client import (
    get_llm,
    get_rag_context,
)

from .tools import (
    portfolio_summary_tool,
    risk_analysis_tool,
    sector_analysis_tool,
    portfolio_performance_tool,
    stock_news_tool,
    stock_market_tool,
    stock_explanation_tool,
)


# ============================================================
# TOOLS
# ============================================================

TOOLS = [
    portfolio_summary_tool,
    risk_analysis_tool,
    sector_analysis_tool,
    portfolio_performance_tool,
    stock_news_tool,
    stock_market_tool,
    stock_explanation_tool,
]


TOOL_MAP = {
    portfolio_summary_tool.name:
        portfolio_summary_tool,

    risk_analysis_tool.name:
        risk_analysis_tool,

    sector_analysis_tool.name:
        sector_analysis_tool,

    portfolio_performance_tool.name:
        portfolio_performance_tool,

    stock_news_tool.name:
        stock_news_tool,

    stock_market_tool.name:
        stock_market_tool,

    stock_explanation_tool.name:
        stock_explanation_tool,
}


# ============================================================
# MEMORY
# ============================================================

chat_memory = ChatMemory(
    max_messages=10
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the AI Financial Assistant for the
Zerodha AI Financial Intelligence platform.

You can use:

1. Uploaded portfolio data
2. Portfolio and market tools
3. FAISS RAG financial knowledge
4. Pre-fetched market news


CORE RULES:

- Answer only finance-related questions.
- Always respond in English.
- Never reveal chain-of-thought.
- Never invent financial data.
- Never invent prices, P&L, news, dates or metrics.
- Use uploaded portfolio data for portfolio questions.
- Use RAG for financial education.
- Combine portfolio data and RAG for hybrid questions.
- Use tools when calculations or verified data are needed.
- RAG is not the source of truth for live portfolio values.
- Do not guarantee profits or future returns.
- Use ₹ for Indian currency when appropriate.
- Keep answers clear and professional.


PORTFOLIO QUESTIONS:

Questions about:

- my portfolio
- my holdings
- current value
- investment
- P&L
- return
- sector allocation
- concentration
- diversification
- comparison between holdings

must use uploaded portfolio information whenever available.


RAG QUESTIONS:

Questions such as:

- What is P/E ratio?
- What is diversification?
- What is expected return?
- What is portfolio optimization?

should use relevant retrieved RAG knowledge.


HYBRID QUESTIONS:

Questions such as:

- Explain concentration risk based on my portfolio.
- Is my portfolio diversified?
- Explain diversification and relate it to my holdings.

should combine actual portfolio information with relevant
financial concepts from RAG.


IMPORTANT:

Never say portfolio information could not be found in the
financial documents when uploaded portfolio data already
contains the required information.
"""


# ============================================================
# GET TOOL-ENABLED LLM
# ============================================================

def get_llm_with_tools():

    return get_llm().bind_tools(
        TOOLS
    )


# ============================================================
# PORTFOLIO CONTEXT
# ============================================================

def build_portfolio_context(
    portfolio_data
):

    if not portfolio_data:

        return (
            "No uploaded portfolio data is available."
        )

    lines = []

    for index, holding in enumerate(
        portfolio_data,
        start=1,
    ):

        if not isinstance(
            holding,
            dict,
        ):
            continue

        symbol = holding.get(
            "Stock Symbol",
            "Unknown"
        )

        quantity = holding.get(
            "Quantity"
        )

        average_price = holding.get(
            "Average Price"
        )

        current_price = holding.get(
            "Current Price"
        )

        sector = holding.get(
            "Sector"
        )

        pnl = holding.get(
            "P&L"
        )

        investment = None
        current_value = None

        # ----------------------------------------------------
        # INVESTMENT
        # ----------------------------------------------------

        try:

            if (
                quantity is not None
                and average_price is not None
            ):

                investment = (
                    float(quantity)
                    * float(average_price)
                )

        except (
            TypeError,
            ValueError,
        ):

            investment = None

        # ----------------------------------------------------
        # CURRENT VALUE
        # ----------------------------------------------------

        try:

            if (
                quantity is not None
                and current_price is not None
            ):

                current_value = (
                    float(quantity)
                    * float(current_price)
                )

        except (
            TypeError,
            ValueError,
        ):

            current_value = None

        details = [
            f"Stock Symbol={symbol}"
        ]

        if quantity is not None:

            details.append(
                f"Quantity={quantity}"
            )

        if average_price is not None:

            details.append(
                f"Average Price={average_price}"
            )

        if current_price is not None:

            details.append(
                f"Current Price={current_price}"
            )

        if investment is not None:

            details.append(
                f"Investment={investment:.2f}"
            )

        if current_value is not None:

            details.append(
                f"Current Value={current_value:.2f}"
            )

        if sector:

            details.append(
                f"Sector={sector}"
            )

        if pnl is not None:

            details.append(
                f"P&L={pnl}"
            )

        lines.append(
            f"{index}. "
            + " | ".join(details)
        )

    if not lines:

        return (
            "No usable uploaded portfolio "
            "data is available."
        )

    return "\n".join(
        lines
    )


# ============================================================
# NEWS CONTEXT
# ============================================================

def build_news_context(
    news_data
):

    if not news_data:

        return (
            "No pre-fetched news is available."
        )

    lines = []

    for symbol, articles in (
        news_data.items()
    ):

        if not articles:

            continue

        lines.append(
            f"Stock: {symbol}"
        )

        for article in articles[:5]:

            if not isinstance(
                article,
                dict,
            ):
                continue

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

            parts = []

            if title:

                parts.append(
                    f"Title={title}"
                )

            if description:

                parts.append(
                    f"Description={description}"
                )

            if source:

                parts.append(
                    f"Source={source}"
                )

            if published:

                parts.append(
                    f"Published={published}"
                )

            if parts:

                lines.append(
                    " | ".join(parts)
                )

    if not lines:

        return (
            "No usable pre-fetched news "
            "is available."
        )

    return "\n".join(
        lines
    )


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute_tool(
    tool_call,
    portfolio_data,
):

    tool_name = tool_call.get(
        "name"
    )

    tool_args = tool_call.get(
        "args",
        {},
    )

    tool = TOOL_MAP.get(
        tool_name
    )

    if tool is None:

        return {
            "status": "error",
            "message": (
                f"Unknown tool: {tool_name}"
            ),
        }

    # --------------------------------------------------------
    # NEWS
    # --------------------------------------------------------

    if tool_name == (
        stock_news_tool.name
    ):

        symbol = tool_args.get(
            "symbol"
        )

        if not symbol:

            return {
                "status": "unavailable",
                "message": (
                    "Stock symbol is required."
                ),
            }

        return tool.invoke(
            {
                "symbol": symbol
            }
        )

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    if tool_name == (
        stock_market_tool.name
    ):

        symbol = tool_args.get(
            "symbol"
        )

        if not symbol:

            return {
                "status": "unavailable",
                "message": (
                    "Stock symbol is required."
                ),
            }

        return tool.invoke(
            {
                "symbol": symbol
            }
        )

    # --------------------------------------------------------
    # STOCK EXPLANATION
    # --------------------------------------------------------

    if tool_name == (
        stock_explanation_tool.name
    ):

        symbol = tool_args.get(
            "symbol"
        )

        if not symbol:

            return {
                "status": "unavailable",
                "message": (
                    "Stock symbol is required."
                ),
            }

        return tool.invoke(
            {
                "symbol": symbol,
                "portfolio_data":
                    portfolio_data,
            }
        )

    # --------------------------------------------------------
    # PORTFOLIO TOOLS
    # --------------------------------------------------------

    if not portfolio_data:

        return {
            "status": "unavailable",
            "message": (
                "Uploaded portfolio data "
                "is not available."
            ),
        }

    try:

        return tool.invoke(
            {
                "portfolio_data":
                    portfolio_data
            }
        )

    except Exception as error:

        return {
            "status": "error",
            "message": str(error),
        }


# ============================================================
# NORMALIZE LLM CONTENT
# ============================================================

def extract_text(
    response
):

    content = getattr(
        response,
        "content",
        ""
    )

    if isinstance(
        content,
        str,
    ):

        return content.strip()

    if isinstance(
        content,
        list,
    ):

        parts = []

        for block in content:

            if isinstance(
                block,
                str,
            ):

                parts.append(
                    block
                )

            elif isinstance(
                block,
                dict,
            ):

                text = block.get(
                    "text"
                )

                if text:

                    parts.append(
                        text
                    )

        return "\n".join(
            parts
        ).strip()

    return str(
        content or ""
    ).strip()


# ============================================================
# FALLBACK FINAL SYNTHESIS
# ============================================================

def generate_fallback_answer(
    user_question,
    portfolio_context,
    rag_context,
    news_context,
    tool_results,
):
    """
    Important fallback.

    Some OpenRouter/free models may successfully call a tool
    but return an empty final content field afterwards.

    This function performs one final NON-TOOL LLM call using
    all collected context and tool results.
    """

    llm = get_llm()

    tool_text = (
        "\n\n".join(tool_results)
        if tool_results
        else "No tools were used."
    )

    fallback_prompt = f"""
Answer the user's financial question using the information
provided below.

Do NOT call tools.
Return ONLY the final answer.

USER QUESTION:
{user_question}


UPLOADED PORTFOLIO:
{portfolio_context}


RAG FINANCIAL KNOWLEDGE:
{
    rag_context
    if rag_context
    else "No relevant RAG context."
}


NEWS:
{news_context}


TOOL RESULTS:
{tool_text}


RULES:

- Use portfolio data for portfolio-specific facts.
- Use RAG only for general financial knowledge.
- Combine both when relevant.
- Do not invent missing financial information.
- Do not say portfolio information was unavailable if it is
  clearly provided above.
- Use ₹ for Indian currency.
- Keep the answer clear and professional.
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=SYSTEM_PROMPT
            ),
            HumanMessage(
                content=fallback_prompt
            ),
        ]
    )

    return extract_text(
        response
    )


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def run_chat_chain(
    user_question: str,
    portfolio_data: list[dict] | None = None,
    news_data: dict | None = None,
):

    # ========================================================
    # VALIDATION
    # ========================================================

    if (
        not user_question
        or not user_question.strip()
    ):

        return (
            "Please enter a financial question."
        )

    user_question = (
        user_question.strip()
    )

    portfolio_data = (
        portfolio_data or []
    )

    news_data = (
        news_data or {}
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    portfolio_context = (
        build_portfolio_context(
            portfolio_data
        )
    )

    news_context = (
        build_news_context(
            news_data
        )
    )

    # ========================================================
    # RAG
    # ========================================================

    try:

        rag_context = get_rag_context(
            user_question,
            k=4,
        )

    except Exception as error:

        print(
            "RAG retrieval failed: "
            f"{error}"
        )

        rag_context = ""

    # ========================================================
    # MEMORY
    # ========================================================

    try:

        chat_history = (
            chat_memory.get_history()
        )

    except Exception:

        chat_history = []

    # ========================================================
    # USER CONTEXT
    # ========================================================

    context_message = f"""
USER QUESTION
============================================================
{user_question}


UPLOADED PORTFOLIO DATA
============================================================
{portfolio_context}


RAG FINANCIAL KNOWLEDGE
============================================================
{
    rag_context
    if rag_context
    else "No relevant RAG documents were retrieved."
}


PRE-FETCHED NEWS
============================================================
{news_context}


IMPORTANT:

- Use uploaded portfolio data for portfolio questions.
- Use RAG for financial education.
- Combine both for hybrid questions.
- Never replace portfolio facts with generic RAG information.
- Do not invent missing data.
- Return only the final answer.
"""

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        *chat_history,
        HumanMessage(
            content=context_message
        ),
    ]

    # ========================================================
    # TOOL-ENABLED LLM
    # ========================================================

    try:

        llm_with_tools = (
            get_llm_with_tools()
        )

        response = (
            llm_with_tools.invoke(
                messages
            )
        )

    except Exception as error:

        print(
            "Initial LLM error: "
            f"{error}"
        )

        return (
            "AI service is temporarily "
            "unavailable."
        )

    messages.append(
        response
    )

    # Store tool results for fallback generation
    tool_results = []

    # ========================================================
    # TOOL LOOP
    # ========================================================

    for _ in range(3):

        tool_calls = getattr(
            response,
            "tool_calls",
            None,
        )

        if not tool_calls:

            break

        for tool_call in tool_calls:

            result = execute_tool(
                tool_call,
                portfolio_data,
            )

            result_text = str(
                result
            )

            tool_results.append(
                result_text
            )

            messages.append(
                ToolMessage(
                    content=result_text,
                    tool_call_id=(
                        tool_call["id"]
                    ),
                )
            )

        try:

            response = (
                llm_with_tools.invoke(
                    messages
                )
            )

        except Exception as error:

            print(
                "Tool follow-up error: "
                f"{error}"
            )

            break

        messages.append(
            response
        )

    # ========================================================
    # TRY NORMAL ANSWER
    # ========================================================

    answer = extract_text(
        response
    )

    # ========================================================
    # IMPORTANT FIX:
    # EMPTY TOOL RESPONSE → NON-TOOL FINAL SYNTHESIS
    # ========================================================

    if not answer:

        print(
            "Tool response contained no final text. "
            "Running fallback synthesis..."
        )

        try:

            answer = generate_fallback_answer(
                user_question=user_question,
                portfolio_context=portfolio_context,
                rag_context=rag_context,
                news_context=news_context,
                tool_results=tool_results,
            )

        except Exception as error:

            print(
                "Fallback synthesis failed: "
                f"{error}"
            )

            answer = ""

    # ========================================================
    # FINAL SAFETY FALLBACK
    # ========================================================

    if not answer:

        return (
            "I could not generate a response "
            "from the available portfolio and "
            "financial information."
        )

    # ========================================================
    # MEMORY
    # ========================================================

    try:

        chat_memory.add_user_message(
            user_question
        )

        chat_memory.add_ai_message(
            answer
        )

    except Exception as error:

        print(
            "Chat memory warning: "
            f"{error}"
        )

    return answer


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("ZERODHA AI - HYBRID CHAT TEST")
    print("=" * 70)

    sample_portfolio = [
        {
            "Stock Symbol": "TCS",
            "Quantity": 10,
            "Average Price": 3500,
            "Current Price": 3800,
            "Sector": (
                "Information Technology"
            ),
        },
        {
            "Stock Symbol": "INFY",
            "Quantity": 15,
            "Average Price": 1450,
            "Current Price": 1600,
            "Sector": (
                "Information Technology"
            ),
        },
        {
            "Stock Symbol": "RELIANCE",
            "Quantity": 8,
            "Average Price": 2450,
            "Current Price": 2900,
            "Sector": "Energy",
        },
    ]

    question = input(
        "\nEnter your question: "
    )

    print(
        "\nAnalyzing...\n"
    )

    result = run_chat_chain(
        user_question=question,
        portfolio_data=sample_portfolio,
    )

    print("=" * 70)
    print("AI ANSWER")
    print("=" * 70)

    print(
        result
    )