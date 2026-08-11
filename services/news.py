import yfinance as yf
import streamlit as st


def get_stock_news(symbol):
    """
    Fetch latest stock news using Yahoo Finance through yfinance.

    Example:
        TCS -> TCS.NS
        RELIANCE -> RELIANCE.NS
    """

    try:
        # -----------------------------------------
        # Clean stock symbol
        # -----------------------------------------
        symbol = str(symbol).strip().upper()

        # -----------------------------------------
        # Add .NS for Indian NSE stocks
        # -----------------------------------------
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            yf_symbol = symbol + ".NS"
        else:
            yf_symbol = symbol

        # DEBUG
        st.write("DEBUG YFINANCE SYMBOL:", yf_symbol)

        # -----------------------------------------
        # Create yfinance ticker
        # -----------------------------------------
        ticker = yf.Ticker(yf_symbol)

        # -----------------------------------------
        # Get latest news
        # -----------------------------------------
        news_data = ticker.get_news(count=5)

        # DEBUG
        st.write("DEBUG NEWS COUNT:", len(news_data))

        # -----------------------------------------
        # Check if news is available
        # -----------------------------------------
        if not news_data:
            st.info(f"ℹ️ No latest news available for {symbol}")
            return []

        articles = []

        # -----------------------------------------
        # Convert yfinance response
        # into your existing article format
        # -----------------------------------------
        for item in news_data:

            # yfinance can have different structures,
            # so we safely extract the required fields.
            content = item.get("content", {})

            title = content.get("title")

            # Publisher/source
            provider = content.get("provider", {})
            source = provider.get("displayName")

            # URL
            click_url = content.get("clickThroughUrl", {})
            url = click_url.get("url")

            # Published date
            published = content.get("pubDate")

            # Description/summary
            description = content.get("summary")

            articles.append({
                "Title": title,
                "Description": description,
                "source": source,
                "published": published,
                "url": url
            })

        # DEBUG
        st.write("DEBUG ARTICLES:", len(articles))

        return articles

    except Exception as e:

        st.error(f"❌ yFinance News Error: {e}")

        return []
