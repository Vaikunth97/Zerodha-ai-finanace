from .memory import ChatMemory
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

from .client import llm, get_rag_context  # [CHANGED] + get_rag_context

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
chat_memory = ChatMemory(max_messages=10)


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

16. RAG context below is general financial education only —
    never treat it as the source of truth for the user's
    current portfolio, prices, or news.


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


RESPONSE STYLE:

For P&L questions, provide only relevant P&L information.

For risk questions, provide only relevant risk information.

For sector questions, provide only relevant sector information.

For news questions, provide the relevant recent news
with source and date when available.

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

This tool combines verified market data, recent news,
and portfolio performance context.

Do not invent a reason for price movement.

Clearly distinguish reported news from confirmed causes.
"""


# ============================================================
# LLM WITH TOOLS
# ============================================================

llm_with_tools = llm.bind_tools(TOOLS)


# ============================================================
# TOOL EXECUTION
# ============================================================
def execute_tool(tool_call, portfolio_data):

    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})

    tool = TOOL_MAP.get(tool_name)

    if tool is None:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}"
        }

    # NEWS
    if tool_name == stock_news_tool.name:
        symbol = tool_args.get("symbol")

        if not symbol:
            return {
                "status": "unavailable",
                "message": "Stock symbol is required."
            }

        return tool.invoke({
            "symbol": symbol
        })

    # MARKET
    if tool_name == stock_market_tool.name:
        symbol = tool_args.get("symbol")

        if not symbol:
            return {
                "status": "unavailable",
                "message": "Stock symbol is required."
            }

        return tool.invoke({
            "symbol": symbol
        })

    # STOCK EXPLANATION
    if tool_name == stock_explanation_tool.name:
        symbol = tool_args.get("symbol")

        if not symbol:
            return {
                "status": "unavailable",
                "message": "Stock symbol is required."
            }

        return tool.invoke({
            "symbol": symbol,
            "portfolio_data": portfolio_data
        })

    # PORTFOLIO TOOLS
    if not portfolio_data:
        return {
            "status": "unavailable",
            "message": "Portfolio data is not available."
        }

    return tool.invoke({
        "portfolio_data": portfolio_data
    })
# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def run_chat_chain(
    user_question: str,
    portfolio_data: list[dict] | None = None,
    news_data: dict | None = None,
):
    portfolio_data = portfolio_data or []

    chat_history = chat_memory.get_history()

    # ========================================================
    # RAG RETRIEVAL  [NEW]
    # ========================================================

    try:
        rag_context = get_rag_context(user_question, k=4)
    except Exception:
        rag_context = ""

    # ========================================================
    # PORTFOLIO CONTEXT
    # ========================================================

    portfolio_context = "No portfolio data is available."

    if portfolio_data:
        symbols = []

        for holding in portfolio_data:
            symbol = holding.get("Stock Symbol")

            if symbol:
                symbols.append(str(symbol))

        if symbols:
            portfolio_context = (
                "The user's uploaded portfolio contains these holdings: "
                + ", ".join(symbols)
                + "."
            )
    news_context = "No pre-fetched news is available."
    if news_data:
        news_context = str(news_data)

    # ========================================================
    # BUILD MESSAGES  [FIX] moved out of the nested if-blocks
    # so `messages` is always defined, even when portfolio_data
    # is empty or has no row with a "Stock Symbol" key.
    # ========================================================

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *chat_history,
        HumanMessage(
            content=f"""
    User Question:

    {user_question}

    Portfolio Context:

    {portfolio_context}

    General Financial Knowledge (RAG):

    {rag_context if rag_context else "No relevant documents were retrieved."}
    Pre-fetched News (from UI):        
    {news_context}
    IMPORTANT:
    - The user's portfolio has already been uploaded.
    - Do NOT ask the user to provide or upload the portfolio again.
    - If the user says "my portfolio", "my holdings", or "my stocks",
    use the uploaded portfolio context.
    - Use the appropriate verified tool when required.
    - Do not guess missing financial data.
    - Use the RAG context only for general financial education,
    never as the source of truth for portfolio numbers.
    """
        ),
    ]

    # ========================================================
    # FIRST LLM CALL
    # ========================================================

    response = llm_with_tools.invoke(messages)

    messages.append(response)


    # ========================================================
    # TOOL CALLS
    # ========================================================

    if response.tool_calls:

        for tool_call in response.tool_calls:

            result = execute_tool(
                tool_call,
                portfolio_data
            )

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )


        # ====================================================
        # SECOND LLM CALL
        # ====================================================
        final_response = llm_with_tools.invoke(messages)

        answer = final_response.content.strip()

        chat_memory.add_user_message(user_question)
        chat_memory.add_ai_message(answer)

        return answer


    # ========================================================
    # NO TOOL REQUIRED
    # ========================================================

    answer = response.content.strip()

    chat_memory.add_user_message(user_question)
    chat_memory.add_ai_message(answer)

    return answer