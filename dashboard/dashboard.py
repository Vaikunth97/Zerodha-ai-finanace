# ============================================================
# dashboard/dashboard.py
# AI Financial Intelligence Dashboard
# ============================================================
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Financial Intelligence",
    page_icon="📊",
    layout="wide"
)
# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown(
    """
    <style>

    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 15px;
        color: #777;
        margin-bottom: 20px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.20);
        border-radius: 12px;
        padding: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)
# ============================================================
# PORTFOLIO SERVICE
# ============================================================
from services.portfolio import (
    read_portfolio,
    valid_coloumn,
    clean_data
)
# ============================================================
# HELPER - FIND COLUMN
# ============================================================
def find_column(df, possible_names):

    columns = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for name in possible_names:

        key = str(name).strip().lower()

        if key in columns:
            return columns[key]

    return None
# ============================================================
# STOCK COLUMN
# ============================================================
def get_stock_column(df):

    return find_column(
        df,
        [
            "Stock",
            "Stock Symbol",
            "Symbol",
            "Ticker",
            "Yahoo Symbol"
        ]
    )


# ============================================================
# QUANTITY COLUMN
# ============================================================
def get_quantity_column(df):

    return find_column(
        df,
        [
            "Quantity",
            "Qty"
        ]
    )
# ============================================================
# BUY PRICE COLUMN
# ============================================================
def get_buy_price_column(df):

    return find_column(
        df,
        [
            "Average Price",
            "Buy Price",
            "Purchase Price",
            "AveragePrice"
        ]
    )

# ============================================================
# CURRENT PRICE COLUMN
# ============================================================

def get_current_price_column(df):

    return find_column(
        df,
        [
            "Current Price",
            "CurrentPrice",
            "Live Price"
        ]
    )
# ============================================================
# SECTOR COLUMN
# ============================================================
def get_sector_column(df):

    return find_column(
        df,
        [
            "Sector"
        ]
    )
# ============================================================
# YAHOO SYMBOL
# ============================================================

def get_yahoo_symbol(stock):

    if not stock:
        return None

    stock = str(stock).strip().upper()

    if stock.endswith(".NS"):
        return stock

    if stock.endswith(".BO"):
        return stock

    return f"{stock}.NS"
# ============================================================
# CURRENT PRICE
# ============================================================
def get_current_price(stock):

    yahoo_symbol = get_yahoo_symbol(stock)

    if not yahoo_symbol:
        return None

    try:

        ticker = yf.Ticker(
            yahoo_symbol
        )

        history = ticker.history(
            period="5d",
            auto_adjust=False
        )

        if history.empty:
            return None

        close_prices = (
            history["Close"]
            .dropna()
        )

        if close_prices.empty:
            return None

        return float(
            close_prices.iloc[-1]
        )

    except Exception:

        return None
# ============================================================
# UPDATE CURRENT PRICES
# ============================================================
def update_prices(df):

    df = df.copy()

    stock_col = get_stock_column(df)

    if stock_col is None:
        return df

    current_price_col = (
        get_current_price_column(df)
    )

    if current_price_col is None:
        current_price_col = "Current Price"

    prices = {}

    stocks = (
        df[stock_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    for stock in stocks:

        prices[stock] = (
            get_current_price(stock)
        )

    df[current_price_col] = (
        df[stock_col]
        .astype(str)
        .str.strip()
        .map(prices)
    )

    return df
# ============================================================
# CALCULATE PORTFOLIO VALUES
# ============================================================
def calculate_portfolio_values(df):

    df = df.copy()

    quantity_col = get_quantity_column(df)

    buy_price_col = get_buy_price_column(df)

    current_price_col = (
        get_current_price_column(df)
    )

    if quantity_col is None:
        return df

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    df[quantity_col] = pd.to_numeric(
        df[quantity_col],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Investment
    # --------------------------------------------------------

    if buy_price_col is not None:

        df[buy_price_col] = pd.to_numeric(
            df[buy_price_col],
            errors="coerce"
        ).fillna(0)

        df["Investment"] = (
            df[quantity_col]
            * df[buy_price_col]
        )
    # --------------------------------------------------------
    # Current Value
    # --------------------------------------------------------
    if current_price_col is not None:
        df[current_price_col] = pd.to_numeric(
            df[current_price_col],
            errors="coerce"
        )
        df["Current Value"] = (
            df[quantity_col]
            * df[current_price_col]
        )
    # --------------------------------------------------------
    # Profit / Loss
    # --------------------------------------------------------
    if (
        "Investment" in df.columns
        and "Current Value" in df.columns
    ):

        df["Profit/Loss"] = (
            df["Current Value"]
            - df["Investment"]
        )
        df["P&L %"] = 0.0
        mask = (
            df["Investment"] != 0
        )

        df.loc[mask, "P&L %"] = (
            df.loc[mask, "Profit/Loss"]
            / df.loc[mask, "Investment"]
        ) * 100

    return df
# ============================================================
# PORTFOLIO SUMMARY
# ============================================================
def get_portfolio_summary(df):
    total_investment = 0.0
    current_value = 0.0
    profit_loss = 0.0
    if "Investment" in df.columns:

        total_investment = float(
            df["Investment"].sum()
        )

    if "Current Value" in df.columns:

        current_value = float(
            df["Current Value"].sum()
        )

    if "Profit/Loss" in df.columns:

        profit_loss = float(
            df["Profit/Loss"].sum()
        )

    if total_investment != 0:

        profit_loss_percentage = (
            profit_loss
            / total_investment
        ) * 100

    else:

        profit_loss_percentage = 0.0

    return (
        total_investment,
        current_value,
        profit_loss,
        profit_loss_percentage
    )
# ============================================================
# TOP GAINERS
# ============================================================
def get_top_gainers(df):
    stock_col = get_stock_column(df)

    if (
        stock_col is None
        or "Profit/Loss" not in df.columns
    ):

        return pd.DataFrame()

    result = df[
        [
            stock_col,
            "Current Price",
            "Profit/Loss",
            "P&L %"
        ]
    ].copy()

    result = result.sort_values(
        "Profit/Loss",
        ascending=False
    )

    return result.head(5)
# ============================================================
# TOP LOSERS
# ============================================================

def get_top_losers(df):

    stock_col = get_stock_column(df)

    if (
        stock_col is None
        or "Profit/Loss" not in df.columns
    ):

        return pd.DataFrame()

    result = df[
        [
            stock_col,
            "Current Price",
            "Profit/Loss",
            "P&L %"
        ]
    ].copy()

    result = result.sort_values(
        "Profit/Loss",
        ascending=True
    )

    return result.head(5)
# ============================================================
# SECTOR ALLOCATION
# ============================================================

def get_sector_data(df):

    sector_col = get_sector_column(df)

    if (
        sector_col is None
        or "Current Value" not in df.columns
    ):

        return pd.DataFrame()

    sector_df = (
        df.groupby(sector_col)[
            "Current Value"
        ]
        .sum()
        .reset_index()
    )

    sector_df.rename(
        columns={
            sector_col: "Sector",
            "Current Value": "Value"
        },
        inplace=True
    )

    return sector_df
# ============================================================
# YFINANCE NEWS
# ============================================================

def get_stock_news_clean(
    stock,
    limit=5
):

    yahoo_symbol = get_yahoo_symbol(
        stock
    )

    if not yahoo_symbol:
        return []

    try:

        ticker = yf.Ticker(
            yahoo_symbol
        )

        raw_news = ticker.news

    except Exception:

        return []

    if not raw_news:
        return []

    articles = []

    for item in raw_news[:limit]:

        try:

            content = item.get(
                "content",
                {}
            )

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = content.get(
                "title",
                item.get(
                    "title",
                    ""
                )
            )

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = content.get(
                "summary",
                item.get(
                    "description",
                    ""
                )
            )

            # ------------------------------------------------
            # SOURCE
            # ------------------------------------------------

            provider = content.get(
                "provider",
                {}
            )

            if isinstance(
                provider,
                dict
            ):

                source = provider.get(
                    "displayName",
                    "Unknown"
                )

            else:

                source = str(
                    provider
                )

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            published = content.get(
                "pubDate",
                ""
            )

            # ------------------------------------------------
            # URL
            # ------------------------------------------------

            canonical = content.get(
                "canonicalUrl",
                {}
            )

            if isinstance(
                canonical,
                dict
            ):

                url = canonical.get(
                    "url",
                    ""
                )

            else:

                url = ""

            if not url:

                url = item.get(
                    "link",
                    item.get(
                        "url",
                        ""
                    )
                )

            # ------------------------------------------------
            # CLEAN ARTICLE
            # ------------------------------------------------

            title = str(
                title
            ).strip()

            description = str(
                description
            ).strip()

            source = str(
                source
            ).strip()

            published = str(
                published
            ).strip()

            url = str(
                url
            ).strip()

            # Ignore completely empty articles

            if (
                not title
                and not description
            ):

                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "source": source,
                    "published": published,
                    "url": url
                }
            )

        except Exception:

            continue

    return articles


# ============================================================
# FETCH NEWS FOR ENTIRE PORTFOLIO
# ============================================================

def fetch_all_news(df):

    news_data = {}

    stock_col = get_stock_column(df)

    if stock_col is None:
        return news_data

    stocks = (
        df[stock_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    for stock in stocks:

        news_data[stock] = (
            get_stock_news_clean(
                stock,
                limit=5
            )
        )

    return news_data


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        """
        <div class="main-title">
            📊 AI Financial Intelligence
        </div>

        <div class="subtitle">
            Portfolio Analytics • Live Market Data • News • AI
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.header(
            "📁 Portfolio"
        )

        uploaded_file = st.file_uploader(
            "Upload Portfolio",
            type=[
                "csv",
                "xlsx"
            ]
        )

        st.divider()

        refresh_button = st.button(
            "🔄 Refresh Market Data",
            use_container_width=True
        )


    # ========================================================
    # NO FILE
    # ========================================================

    if uploaded_file is None:

        st.info(
            "📁 Upload your portfolio to begin."
        )

        return


    # ========================================================
    # REFRESH
    # ========================================================

    if refresh_button:

        st.session_state.pop(
            "portfolio_data",
            None
        )

        st.session_state.pop(
            "news_data",
            None
        )

        st.rerun()


    # ========================================================
    # PROCESS PORTFOLIO
    # ========================================================

    if "portfolio_data" not in st.session_state:

        # ----------------------------------------------------
        # READ PORTFOLIO
        # ----------------------------------------------------

        with st.spinner(
            "📂 Reading portfolio..."
        ):

            try:

                portfolio = read_portfolio(
                    uploaded_file
                )

            except Exception as e:

                st.error(
                    f"Unable to read portfolio: {e}"
                )

                return


        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        try:

            missing_columns = valid_coloumn(
                portfolio
            )

        except Exception:

            missing_columns = []


        if missing_columns:

            st.error(
                "Missing required columns: "
                f"{missing_columns}"
            )

            return


        # ----------------------------------------------------
        # CLEAN DATA
        # ----------------------------------------------------

        try:

            portfolio = clean_data(
                portfolio
            )

        except Exception as e:

            st.error(
                f"Data cleaning failed: {e}"
            )

            return


        # ----------------------------------------------------
        # CURRENT MARKET PRICES
        # ----------------------------------------------------

        with st.spinner(
            "💹 Fetching current market prices..."
        ):

            portfolio = update_prices(
                portfolio
            )


        # ----------------------------------------------------
        # CALCULATE VALUES
        # ----------------------------------------------------

        portfolio = (
            calculate_portfolio_values(
                portfolio
            )
        )


        # ----------------------------------------------------
        # LATEST NEWS
        # ----------------------------------------------------

        with st.spinner(
            "📰 Fetching latest market news..."
        ):

            news_data = fetch_all_news(
                portfolio
            )


        # ----------------------------------------------------
        # SAVE TO SESSION
        # ----------------------------------------------------

        st.session_state[
            "portfolio_data"
        ] = portfolio

        st.session_state[
            "news_data"
        ] = news_data


    # ========================================================
    # LOAD SESSION DATA
    # ========================================================

    portfolio = st.session_state[
        "portfolio_data"
    ]

    news_data = st.session_state[
        "news_data"
    ]


    # ========================================================
    # SUMMARY VALUES
    # ========================================================

    (
        total_investment,
        current_value,
        profit_loss,
        profit_loss_percentage
    ) = get_portfolio_summary(
        portfolio
    )


    # ========================================================
    # 1. PORTFOLIO OVERVIEW
    # ========================================================

    with st.expander(
        "📌 Portfolio Overview",
        expanded=True
    ):

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            st.metric(
                "Total Stocks",
                len(portfolio)
            )

        with col2:

            st.metric(
                "Total Investment",
                f"₹ {total_investment:,.2f}"
            )

        with col3:

            st.metric(
                "Current Value",
                f"₹ {current_value:,.2f}"
            )

        with col4:

            st.metric(
                "Profit / Loss",
                f"₹ {profit_loss:,.2f}",
                f"{profit_loss_percentage:.2f}%"
            )


        st.divider()


        # ----------------------------------------------------
        # INVESTMENT VS CURRENT VALUE
        # ----------------------------------------------------

        st.subheader(
            "📊 Investment vs Current Value"
        )

        performance_df = pd.DataFrame(
            {
                "Category": [
                    "Investment",
                    "Current Value"
                ],
                "Value": [
                    total_investment,
                    current_value
                ]
            }
        )

        performance_fig = px.bar(
            performance_df,
            x="Category",
            y="Value",
            text_auto=".2s"
        )

        performance_fig.update_layout(
            height=400,
            xaxis_title="",
            yaxis_title="Value (₹)"
        )

        st.plotly_chart(
            performance_fig,
            use_container_width=True
        )


        # ----------------------------------------------------
        # SECTOR ALLOCATION
        # ----------------------------------------------------

        left_col, right_col = (
            st.columns(2)
        )


        with left_col:

            st.subheader(
                "🥧 Sector Allocation"
            )

            sector_df = get_sector_data(
                portfolio
            )

            if not sector_df.empty:

                sector_fig = px.pie(
                    sector_df,
                    names="Sector",
                    values="Value",
                    hole=0.45
                )

                sector_fig.update_layout(
                    height=400
                )

                st.plotly_chart(
                    sector_fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "Sector information is not available."
                )


        # ----------------------------------------------------
        # TOP GAINERS
        # ----------------------------------------------------

        with right_col:

            st.subheader(
                "🏆 Top Gainers"
            )

            gainers = get_top_gainers(
                portfolio
            )

            if not gainers.empty:

                st.dataframe(
                    gainers,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No gainers data available."
                )


        # ----------------------------------------------------
        # TOP LOSERS + P&L
        # ----------------------------------------------------

        left_col, right_col = (
            st.columns(2)
        )


        with left_col:

            st.subheader(
                "📉 Top Losers"
            )

            losers = get_top_losers(
                portfolio
            )

            if not losers.empty:

                st.dataframe(
                    losers,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No losers data available."
                )


        with right_col:

            st.subheader(
                "📊 Stock-wise P&L"
            )

            stock_col = get_stock_column(
                portfolio
            )

            if (
                stock_col is not None
                and "Profit/Loss"
                in portfolio.columns
            ):

                pnl_df = portfolio[
                    [
                        stock_col,
                        "Profit/Loss"
                    ]
                ].copy()

                pnl_df = pnl_df.dropna()

                if not pnl_df.empty:

                    pnl_fig = px.bar(
                        pnl_df,
                        x=stock_col,
                        y="Profit/Loss",
                        text_auto=".2f"
                    )

                    pnl_fig.update_layout(
                        height=400,
                        xaxis_title="Stock",
                        yaxis_title="P&L (₹)"
                    )

                    st.plotly_chart(
                        pnl_fig,
                        use_container_width=True
                    )

                else:

                    st.info(
                        "No P&L data available."
                    )

            else:

                st.info(
                    "P&L data is not available."
                )


        # ----------------------------------------------------
        # PORTFOLIO TABLE
        # ----------------------------------------------------

        st.subheader(
            "📋 Portfolio Holdings"
        )

        st.dataframe(
            portfolio,
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # 2. PORTFOLIO HEALTH
    # ========================================================

    with st.expander(
        "🩺 Portfolio Health"
    ):

        st.write(
            "Analyze the overall health of your portfolio."
        )

        if st.button(
            "Generate Health Score",
            key="health_button"
        ):

            try:

                from AI.health_score import (
                    portfolio_health_score
                )

                with st.spinner(
                    "🤖 Analyzing portfolio health..."
                ):

                    # IMPORTANT:
                    # Pass DataFrame, not string.
                    result = portfolio_health_score(
                        portfolio
                    )

                st.markdown(
                    result
                )

            except Exception as e:

                st.error(
                    f"Health analysis failed: {e}"
                )


    # ========================================================
    # 3. RISK ANALYSIS
    # ========================================================

    with st.expander(
        "⚠️ Risk Analysis"
    ):

        st.write(
            "Analyze portfolio concentration and risk."
        )

        if st.button(
            "Generate Risk Analysis",
            key="risk_button"
        ):

            try:

                from AI.risk_analysis import (
                    portfolio_risk_analysis
                )

                with st.spinner(
                    "🤖 Analyzing portfolio risk..."
                ):

                    result = portfolio_risk_analysis(
                        portfolio
                    )

                st.markdown(
                    result
                )

            except Exception as e:

                st.error(
                    f"Risk analysis failed: {e}"
                )


    # ========================================================
    # 4. AI PORTFOLIO ANALYSIS
    # ========================================================

    with st.expander(
        "🤖 AI Portfolio Analysis"
    ):

        # ----------------------------------------------------
        # PORTFOLIO SUMMARY
        # ----------------------------------------------------

        st.subheader(
            "Portfolio Summary"
        )

        if st.button(
            "Generate Portfolio Summary",
            key="summary_button"
        ):

            try:

                from AI.portfolio_summary import (
                    generate_portfolio_summary
                )

                with st.spinner(
                    "🤖 Generating portfolio summary..."
                ):

                    result = (
                        generate_portfolio_summary(
                            portfolio
                        )
                    )

                st.markdown(
                    result
                )

            except Exception as e:

                st.error(
                    f"Portfolio summary failed: {e}"
                )


        st.divider()


        # ----------------------------------------------------
        # IMPROVEMENT SUGGESTIONS
        # ----------------------------------------------------

        st.subheader(
            "Improvement Suggestions"
        )

        if st.button(
            "Generate Suggestions",
            key="improvement_button"
        ):

            try:

                from AI.improvement import (
                    portfolio_improvement_suggestions
                )

                with st.spinner(
                    "🤖 Generating suggestions..."
                ):

                    result = (
                        portfolio_improvement_suggestions(
                            portfolio
                        )
                    )

                st.markdown(
                    result
                )

            except Exception as e:

                st.error(
                    f"Improvement analysis failed: {e}"
                )


    # ========================================================
    # 5. STOCK ANALYSIS
    # ========================================================

    with st.expander(
        "📈 Stock Analysis"
    ):

        stock_col = get_stock_column(
            portfolio
        )

        if stock_col is None:

            st.warning(
                "Stock column not found."
            )

        else:

            stocks = (
                portfolio[stock_col]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            selected_stock = st.selectbox(
                "Select Stock",
                stocks,
                key="stock_analysis_select"
            )


            # ------------------------------------------------
            # CURRENT PRICE
            # ------------------------------------------------

            current_price = get_current_price(
                selected_stock
            )

            if current_price is not None:

                st.metric(
                    "Current Market Price",
                    f"₹ {current_price:,.2f}"
                )

            else:

                st.warning(
                    "Current market price unavailable."
                )


            # ------------------------------------------------
            # SELECTED STOCK NEWS
            # ------------------------------------------------

            selected_news = news_data.get(
                selected_stock,
                []
            )


            # ------------------------------------------------
            # STOCK AI ANALYSIS
            # ------------------------------------------------

            if st.button(
                "Generate AI Stock Analysis",
                key="stock_analysis_button"
            ):

                try:

                    from AI.stock_explainer import (
                        explain_stock
                    )

                    # ----------------------------------------
                    # Get selected stock DataFrame
                    # ----------------------------------------

                    stock_df = portfolio[
                        portfolio[stock_col]
                        .astype(str)
                        .str.strip()
                        == selected_stock
                    ].copy()


                    # ----------------------------------------
                    # Prepare news
                    # ----------------------------------------

                    news_lines = []

                    for article in selected_news:

                        title = article.get(
                            "title",
                            ""
                        ).strip()

                        description = article.get(
                            "description",
                            ""
                        ).strip()

                        if title:

                            news_lines.append(
                                f"Title: {title}"
                            )

                        if description:

                            news_lines.append(
                                f"Description: {description}"
                            )


                    news_text = "\n".join(
                        news_lines
                    )


                    # ----------------------------------------
                    # Try function with DataFrame + News
                    # ----------------------------------------

                    with st.spinner(
                        "🤖 Analyzing stock..."
                    ):

                        try:

                            result = explain_stock(
                                stock_df,
                                news_text
                            )

                        except TypeError:

                            # Fallback if existing function
                            # accepts only DataFrame.
                            result = explain_stock(
                                stock_df
                            )

                    st.markdown(
                        result
                    )

                except Exception as e:

                    st.error(
                        f"Stock analysis failed: {e}"
                    )


    # ========================================================
    # 6. LATEST NEWS
    # ========================================================

    with st.expander(
        "📰 Latest News"
    ):

        stock_col = get_stock_column(
            portfolio
        )

        if stock_col is None:

            st.warning(
                "Stock column not found."
            )

        else:

            news_stocks = (
                portfolio[stock_col]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            selected_news_stock = st.selectbox(
                "Select Stock",
                news_stocks,
                key="news_stock_select"
            )


            articles = news_data.get(
                selected_news_stock,
                []
            )


            if not articles:

                st.info(
                    "No recent news available for "
                    f"{selected_news_stock}."
                )

            else:

                displayed_articles = 0

                for article in articles:

                    title = str(
                        article.get(
                            "title",
                            ""
                        )
                    ).strip()

                    description = str(
                        article.get(
                            "description",
                            ""
                        )
                    ).strip()

                    source = str(
                        article.get(
                            "source",
                            ""
                        )
                    ).strip()

                    published = str(
                        article.get(
                            "published",
                            ""
                        )
                    ).strip()

                    url = str(
                        article.get(
                            "url",
                            ""
                        )
                    ).strip()


                    # Don't show empty cards
                    if (
                        not title
                        and not description
                    ):

                        continue


                    displayed_articles += 1


                    # ------------------------------------------------
                    # TITLE
                    # ------------------------------------------------

                    if title:

                        st.markdown(
                            f"### 📰 {title}"
                        )


                    # ------------------------------------------------
                    # DESCRIPTION
                    # ------------------------------------------------

                    if description:

                        st.write(
                            description
                        )


                    # ------------------------------------------------
                    # SOURCE
                    # ------------------------------------------------

                    if source:

                        st.caption(
                            f"Source: {source}"
                        )


                    # ------------------------------------------------
                    # PUBLISHED
                    # ------------------------------------------------

                    if published:

                        st.caption(
                            f"Published: {published}"
                        )


                    # ------------------------------------------------
                    # LINK
                    # ------------------------------------------------

                    if url:

                        st.link_button(
                            "Read Full Article",
                            url
                        )


                    st.divider()


                if displayed_articles == 0:

                    st.info(
                        "News was fetched, but readable "
                        "article information is unavailable."
                    )


    # ========================================================
    # 7. ASK AI
    # ========================================================

    with st.expander(
        "💬 Ask AI",
        expanded=True
    ):

        st.caption(
            "Ask questions using your portfolio, "
            "current market prices and latest news."
        )

        question = st.text_input(
            "Ask your question",
            placeholder=(
                "Example: Why is TCS falling "
                "and what recent news may be affecting it?"
            ),
            key="chat_question"
        )


        if st.button(
            "🤖 Ask AI",
            key="ask_ai_button"
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                try:

                    from AI.chat import (
                        portfolio_chat
                    )

                    with st.spinner(
                        "🤖 Analyzing portfolio and market news..."
                    ):

                        # IMPORTANT:
                        # DataFrame + question + news
                        answer = portfolio_chat(
                            portfolio,
                            question,
                            news_data
                        )

                    st.markdown(
                        "### 🤖 AI Answer"
                    )

                    st.markdown(
                        answer
                    )

                except Exception as e:

                    st.error(
                        f"AI Chat failed: {e}"
                    )


