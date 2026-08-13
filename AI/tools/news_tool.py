from langchain_core.tools import tool

from services.news import get_stock_news


@tool
def stock_news_tool(symbol: str) -> dict:
    """
    Fetch latest news for an Indian stock.

    Use this tool when the user asks about:
    - latest news
    - recent news
    - news about a stock
    - recent developments related to a stock
    """

    if not symbol or not symbol.strip():
        return {
            "status": "unavailable",
            "message": "Stock symbol is required."
        }

    symbol = symbol.strip().upper()

    try:
        articles = get_stock_news(symbol)

        if not articles:
            return {
                "status": "unavailable",
                "symbol": symbol,
                "message": f"No recent news is available for {symbol}."
            }
        clean_articles = []

        symbol_keywords = {
            symbol.lower(),
            symbol.upper().lower(),
        }

        # Company-name keywords
        company_keywords = {
            "TCS": ["tcs", "tata consultancy services", "tata consultancy"],
            "RELIANCE": ["reliance", "reliance industries"],
            "HDFCBANK": ["hdfc bank", "hdfcbank"],
        }

        keywords = symbol_keywords | set(
            company_keywords.get(symbol, [])
        )

        for article in articles:

            title = str(article.get("Title") or "").lower()
            description = str(
                article.get("Description") or ""
            ).lower()

            text = f"{title} {description}"

            # Keep only articles mentioning the stock/company
            if not any(keyword in text for keyword in keywords):
                continue

            clean_articles.append({
                "title": article.get("Title"),
                "description": article.get("Description"),
                "source": article.get("source"),
                "published": article.get("published"),
                "url": article.get("url"),
            })

        # No relevant articles after filtering
        if not clean_articles:
            return {
                "status": "unavailable",
                "symbol": symbol,
                "message": f"No directly relevant recent news is available for {symbol}."
            }

        # Keep latest 5 relevant articles
        clean_articles = clean_articles[:5]

        return {
            "status": "success",
            "symbol": symbol,
            "articles": clean_articles,
        }

    except Exception:
        return {
            "status": "error",
            "symbol": symbol,
            "message": "Unable to fetch stock news."
        }