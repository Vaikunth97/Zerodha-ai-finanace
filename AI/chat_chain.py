from .memory import ChatMemory

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

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
# AVAILABLE TOOLS
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
    portfolio_summary_tool.name: portfolio_summary_tool,
    risk_analysis_tool.name: risk_analysis_tool,
    sector_analysis_tool.name: sector_analysis_tool,
    portfolio_performance_tool.name: portfolio_performance_tool,
    stock_news_tool.name: stock_news_tool,
    stock_market_tool.name: stock_market_tool,
    stock_explanation_tool.name: stock_explanation_tool,
}


# ============================================================
# CHAT MEMORY
# ============================================================

chat_memory = ChatMemory(
    max_messages=10
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an AI Financial Assistant for a portfolio
intelligence platform.

IMPORTANT RULES:

1. Answer only finance-related questions.

2. Always respond in English.

3. Never reveal chain-of-thought or internal reasoning.

4. Never invent financial data.

5. Never invent news, headlines, sources, dates,
   prices, P&L, risk scores, or portfolio metrics.

6. Use the appropriate tool whenever verified
   backend data is required.

7. Treat tool results as the source of truth.

8. If required data is unavailable, clearly say so.

9. Do not guarantee profits or future returns.

10. Financial information is for educational purposes only
    and is not financial advice.

11. Keep responses concise and professional.

12. Answer only what the user asked.

13. Do not add unrelated portfolio information.

14. Use ₹ for Indian currency when appropriate.

15. Keep financial numbers exactly as provided by tools.

16. RAG context is general financial education only.
    Never treat RAG as the source of truth for the user's
    current portfolio, prices, live market information,
    or news.


PORTFOLIO QUESTIONS:

Use portfolio analytics tools for questions about:

- P&L
- investment
- current portfolio value
- portfolio performance
- risk
- risk score
- risk alerts
- sector allocation
- diversification
- portfolio holdings


NEWS QUESTIONS:

Use stock_news_tool when the user asks about:

- latest news
- recent news
- current news
- news about a stock
- recent developments about a company

Never invent news.

Use only information returned by stock_news_tool.

Do not claim that a news article caused a stock price
movement unless the available source explicitly establishes it.


MARKET DATA QUESTIONS:

Use stock_market_tool when the user asks about:

- current stock price
- previous close
- daily change
- daily change percentage
- company information
- sector
- industry
- market capitalization
- P/E ratio
- 52-week high
- 52-week low
- dividend yield

Never invent market data.

Use only information returned by stock_market_tool.


STOCK MOVEMENT QUESTIONS:

When the user asks why a stock moved, what happened to a
holding, or how a stock's movement affects their portfolio:

1. Use stock_market_tool to get current market movement.

2. Use stock_news_tool to get recent news.

3. If portfolio data is available, use the appropriate
   portfolio analytics tool to determine the user's exposure.

4. Do not claim that news caused the price movement unless
   the available source explicitly supports that conclusion.

5. Clearly distinguish:
   - verified market movement
   - reported news
   - portfolio impact
   - uncertainty

6. Never invent a reason for a stock movement.


STOCK EXPLANATION:

Use stock_explanation_tool when the user asks questions such as:

- Why did TCS move?
- Why is TCS moving today?
- What happened to my TCS holding?
- Explain TCS movement.
- How does TCS affect my portfolio?

This tool combines verified market data,
recent news, and portfolio performance context.

Do not invent a reason for price movement.

Clearly distinguish reported news from confirmed causes.


GENERAL FINANCIAL EDUCATION:

For educational questions such as:

- What is P/E ratio?
- What is expected portfolio return?
- What is diversification?
- What is volatility?
- What is an IPO?

Use the provided RAG context when relevant.

If the RAG context does not contain enough information,
say that the financial documents do not contain sufficient
information.

Do not invent definitions supposedly sourced from the
financial documents.
"""


# ============================================================
# LAZY LLM WITH TOOLS
# ============================================================

_llm_with_tools = None


def get_llm_with_tools():
    """
    Get the central OpenRouter LLM and bind tools lazily.

    Lazy loading prevents FastAPI from crashing during import
    if the API key or AI service is temporarily unavailable.
    """

    global _llm_with_tools

    if _llm_with_tools is None:

        llm = get_llm()

        _llm_with_tools = llm.bind_tools(
            TOOLS
        )

    return _llm_with_tools


# ============================================================
# RESPONSE TEXT EXTRACTOR
# ============================================================

def extract_response_text(response) -> str:
    """
    Safely extract text from LangChain AIMessage.
    """

    if response is None:
        return ""

    content = getattr(
        response,
        "content",
        None
    )

    # Normal response
    if isinstance(content, str):
        return content.strip()

    # Structured response
    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, str):

                text_parts.append(
                    item
                )

            elif isinstance(item, dict):

                text = item.get(
                    "text"
                )

                if text:

                    text_parts.append(
                        str(text)
                    )

        return "\n".join(
            text_parts
        ).strip()

    if content is not None:

        return str(
            content
        ).strip()

    return ""


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(
    tool_call,
    portfolio_data
):

    tool_name = tool_call.get(
        "name"
    )

    tool_args = tool_call.get(
        "args",
        {}
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

    # ========================================================
    # NEWS TOOL
    # ========================================================

    if tool_name == stock_news_tool.name:

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

        try:

            return tool.invoke(
                {
                    "symbol": symbol
                }
            )

        except Exception as error:

            return {
                "status": "error",
                "message": str(error),
            }

    # ========================================================
    # MARKET TOOL
    # ========================================================

    if tool_name == stock_market_tool.name:

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

        try:

            return tool.invoke(
                {
                    "symbol": symbol
                }
            )

        except Exception as error:

            return {
                "status": "error",
                "message": str(error),
            }

    # ========================================================
    # STOCK EXPLANATION TOOL
    # ========================================================

    if (
        tool_name
        == stock_explanation_tool.name
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

        try:

            return tool.invoke(
                {
                    "symbol": symbol,
                    "portfolio_data": (
                        portfolio_data
                    ),
                }
            )

        except Exception as error:

            return {
                "status": "error",
                "message": str(error),
            }

    # ========================================================
    # PORTFOLIO TOOLS
    # ========================================================

    if not portfolio_data:

        return {
            "status": "unavailable",
            "message": (
                "Portfolio data is not available."
            ),
        }

    try:

        return tool.invoke(
            {
                "portfolio_data": (
                    portfolio_data
                )
            }
        )

    except Exception as error:

        return {
            "status": "error",
            "message": str(error),
        }


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def run_chat_chain(
    user_question: str,
    portfolio_data: list[dict] | None = None,
    news_data: dict | None = None,
):

    # ========================================================
    # VALIDATE QUESTION
    # ========================================================

    if (
        not user_question
        or not user_question.strip()
    ):

        return (
            "Please enter a financial question."
        )

    portfolio_data = (
        portfolio_data
        or []
    )

    news_data = (
        news_data
        or {}
    )

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    try:

        chat_history = (
            chat_memory.get_history()
        )

    except Exception:

        chat_history = []

    # ========================================================
    # RAG RETRIEVAL
    # ========================================================

    try:

        rag_context = get_rag_context(
            user_question,
            k=4
        )

    except Exception as error:

        print(
            f"RAG context error: {error}"
        )

        rag_context = ""

    # ========================================================
    # PORTFOLIO CONTEXT
    # ========================================================

    portfolio_context = (
        "No portfolio data is available."
    )

    if portfolio_data:

        symbols = []

        for holding in portfolio_data:

            if not isinstance(
                holding,
                dict
            ):
                continue

            symbol = holding.get(
                "Stock Symbol"
            )

            if symbol:

                symbol = str(
                    symbol
                ).strip()

                if (
                    symbol
                    and symbol not in symbols
                ):

                    symbols.append(
                        symbol
                    )

        if symbols:

            portfolio_context = (
                "The user's uploaded portfolio "
                "contains these holdings: "
                + ", ".join(symbols)
                + "."
            )

        else:

            portfolio_context = (
                "Portfolio data is available, "
                "but no stock symbols were found."
            )

    # ========================================================
    # NEWS CONTEXT
    # ========================================================

    news_context = (
        "No pre-fetched news is available."
    )

    if news_data:

        news_context = str(
            news_data
        )

    # ========================================================
    # BUILD MESSAGES
    # ========================================================

    messages = [

        SystemMessage(
            content=SYSTEM_PROMPT
        ),

        *chat_history,

        HumanMessage(
            content=f"""
USER QUESTION:

{user_question}


UPLOADED PORTFOLIO CONTEXT:

{portfolio_context}


GENERAL FINANCIAL KNOWLEDGE FROM RAG:

{rag_context if rag_context else "No relevant financial document context was retrieved."}


PRE-FETCHED NEWS FROM UI:

{news_context}


IMPORTANT INSTRUCTIONS:

- The user's portfolio has already been uploaded when
  portfolio data is available.

- Do not ask the user to upload the portfolio again.

- If the user says "my portfolio", "my holdings",
  or "my stocks", use the uploaded portfolio context.

- Use verified backend tools whenever live or
  portfolio-specific information is required.

- Do not guess missing financial data.

- RAG is only for general financial education.

- Never use RAG as live market information.

- Never use RAG as the user's portfolio data.

- Answer only the question asked.

- Return only the final response.
"""
        ),
    ]

    # ========================================================
    # GET LLM
    # ========================================================

    try:

        llm_with_tools = (
            get_llm_with_tools()
        )

    except Exception as error:

        print(
            f"Unable to initialize LLM: {error}"
        )

        return (
            "AI service is temporarily unavailable."
        )

    # ========================================================
    # FIRST LLM CALL
    # ========================================================

    try:

        response = (
            llm_with_tools.invoke(
                messages
            )
        )

    except Exception as error:

        print(
            f"First AI call failed: {error}"
        )

        return (
            "AI service is temporarily unavailable."
        )

    messages.append(
        response
    )

    # ========================================================
    # TOOL CALLS
    # ========================================================

    tool_calls = getattr(
        response,
        "tool_calls",
        None
    )

    if tool_calls:

        for tool_call in tool_calls:

            result = execute_tool(
                tool_call,
                portfolio_data
            )

            messages.append(

                ToolMessage(
                    content=str(result),
                    tool_call_id=(
                        tool_call.get(
                            "id"
                        )
                    ),
                )

            )

        # ====================================================
        # FINAL RESPONSE AFTER TOOLS
        # ====================================================

        try:

            final_response = (
                llm_with_tools.invoke(
                    messages
                )
            )

        except Exception as error:

            print(
                f"Final AI call failed: {error}"
            )

            return (
                "AI service is temporarily unavailable."
            )

        answer = (
            extract_response_text(
                final_response
            )
        )

    else:

        # ====================================================
        # NO TOOL REQUIRED
        # ====================================================

        answer = (
            extract_response_text(
                response
            )
        )

    # ========================================================
    # EMPTY RESPONSE CHECK
    # ========================================================

    if not answer:

        print(
            "Chat chain received an empty "
            "AI response."
        )

        return (
            "AI did not return a text response."
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
            f"Chat memory update failed: {error}"
        )

    return answer