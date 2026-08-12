# ============================================================
# dashboard/dashboard.py
# AI Financial Intelligence
# UI / ORCHESTRATION ONLY
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px


# ============================================================
# SERVICES
# ============================================================

from services.portfolio import (
    read_portfolio,
    valid_coloumn,
    clean_data
)

from services.market import (
    updated_current_price,
    get_stock_info,
    get_market_data
)

from services.news import (
    get_stock_news
)


# ============================================================
# ANALYTICS
# ============================================================

from Analytics.portfolio_analytics import (
    calculate_total_investment,
    calculate_current_value,
    calculate_profit_loss,
    calculate_profit_loss_percentage,
    calculate_portfolio_summary
)

from Analytics.sector_analysis import (
    compute_sector_breakdown
)


# ============================================================
# PAGE CONFIG
# ============================================================
def main():

    st.set_page_config(
        page_title="AI Financial Intelligence",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


    # ============================================================
    # CUSTOM CSS
    # ============================================================

    st.markdown(
        """
        <style>

        /* Main page */

        .block-container {
            padding-top: 1.5rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }


        /* Header */

        .main-title {
            font-size: 34px;
            font-weight: 700;
            margin-bottom: 0px;
        }

        .subtitle {
            color: #777;
            font-size: 15px;
            margin-bottom: 22px;
        }


        /* KPI cards */

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 14px;
            padding: 16px;
            background: rgba(128,128,128,0.03);
        }


        /* Expanders */

        div[data-testid="stExpander"] {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 14px;
            margin-bottom: 12px;
        }


        /* Buttons */

        .stButton > button {
            border-radius: 9px;
        }


        /* Sidebar */

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,0.15);
        }


        /* Small cards */

        .info-card {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ============================================================
    # SESSION STATE
    # ============================================================

    if "portfolio_data" not in st.session_state:
        st.session_state.portfolio_data = None

    if "news_data" not in st.session_state:
        st.session_state.news_data = {}

    if "file_name" not in st.session_state:
        st.session_state.file_name = None


    # ============================================================
    # HEADER
    # ============================================================

    st.markdown(
        '<div class="main-title">📊 AI Financial Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Portfolio Analytics  •  Market Data  •  News  •  AI Insights'
        '</div>',
        unsafe_allow_html=True
    )


    # ============================================================
    # SIDEBAR
    # ============================================================

    with st.sidebar:

        st.header("📁 Portfolio")

        uploaded_file = st.file_uploader(
            "Upload Portfolio",
            type=["csv", "xlsx"]
        )

        st.divider()

        if st.session_state.portfolio_data is not None:

            st.success("Portfolio loaded")

            if st.session_state.file_name:
                st.caption(
                    f"File: {st.session_state.file_name}"
                )

            refresh = st.button(
                "🔄 Refresh Market Data",
                use_container_width=True
            )

            if refresh:

                try:

                    with st.spinner("Updating market data..."):

                        df = st.session_state.portfolio_data.copy()

                        df = updated_current_price(df)

                        st.session_state.portfolio_data = df

                    st.success("Market data updated")

                except Exception as e:

                    st.error(
                        f"Market data update failed: {e}"
                    )


    # ============================================================
    # LOAD PORTFOLIO
    # ============================================================

    if uploaded_file is not None:

        new_file = (
            st.session_state.file_name
            != uploaded_file.name
        )

        if new_file:

            try:

                with st.spinner("Reading portfolio..."):

                    portfolio = read_portfolio(
                        uploaded_file
                    )


                # ------------------------------------------------
                # Validate
                # ------------------------------------------------

                missing_columns = valid_coloumn(
                    portfolio
                )

                if missing_columns:

                    st.error(
                        "Missing required columns: "
                        + ", ".join(missing_columns)
                    )

                    st.stop()


                # ------------------------------------------------
                # Clean
                # ------------------------------------------------

                portfolio = clean_data(
                    portfolio
                )


                # ------------------------------------------------
                # Market Data
                # ------------------------------------------------

                with st.spinner(
                    "Fetching live market data..."
                ):

                    portfolio = updated_current_price(
                        portfolio
                    )


                # ------------------------------------------------
                # Save in Session State
                # ------------------------------------------------

                st.session_state.portfolio_data = portfolio

                st.session_state.file_name = uploaded_file.name

                st.session_state.news_data = {}


            except Exception as e:

                st.error(
                    f"Unable to process portfolio: {e}"
                )

                st.stop()


    # ============================================================
    # NO PORTFOLIO
    # ============================================================

    if st.session_state.portfolio_data is None:

        st.info(
            "👈 Upload your portfolio from the sidebar to begin."
        )

        st.markdown(
            """
            ### What you can explore

            📈 **Portfolio Overview**  
            Track investment, current value and P&L.

            📊 **Analytics**  
            Understand sectors, gainers, losers and portfolio risk.

            🤖 **AI Insights**  
            Get portfolio health, risk analysis and suggestions.

            📰 **Market News**  
            View latest stock-related news.

            💬 **Ask AI**  
            Ask questions about your portfolio.
            """
        )

        st.stop()


    # ============================================================
    # DATA
    # ============================================================

    portfolio = st.session_state.portfolio_data


    # ============================================================
    # COMMON PORTFOLIO CALCULATIONS
    # IMPORTANT:
    # These calculations are outside Overview.
    # Therefore Analytics can also use them.
    # ============================================================

    try:

        total_investment = calculate_total_investment(
            portfolio
        )

    except Exception:

        total_investment = 0


    try:

        current_value = calculate_current_value(
            portfolio
        )

    except Exception:

        current_value = 0


    try:

        profit_loss = calculate_profit_loss(
            portfolio
        )

    except Exception:

        profit_loss = 0


    try:

        profit_loss_pct = calculate_profit_loss_percentage(
            portfolio
        )

    except Exception:

        profit_loss_pct = 0


    # ============================================================
    # CATEGORY NAVIGATION
    # ============================================================

    st.sidebar.divider()

    st.sidebar.subheader("🧭 Sections")

    section = st.sidebar.radio(
        "Go to",
        [
            "📈 Overview",
            "📊 Analytics",
            "🎯 Benchmark",
            "🤖 AI Insights",
            "📈 Stock Analysis",
            "📰 Market News",
            "💬 Ask AI"
        ]
    )


    # ============================================================
    # 1. OVERVIEW
    # ============================================================

    if section == "📈 Overview":

        st.header("📈 Portfolio Overview")


        # --------------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "💰 Total Investment",
                f"₹ {total_investment:,.2f}"
            )

        with col2:

            st.metric(
                "📊 Current Value",
                f"₹ {current_value:,.2f}"
            )

        with col3:

            st.metric(
                "💹 Profit / Loss",
                f"₹ {profit_loss:,.2f}"
            )

        with col4:

            st.metric(
                "📈 Return",
                f"{profit_loss_pct:.2f}%"
            )


        st.divider()


        # --------------------------------------------------------
        # VALUE CHART + HOLDINGS
        # --------------------------------------------------------

        left, right = st.columns(2)


        # --------------------------------------------------------
        # Investment vs Current Value
        # --------------------------------------------------------

        with left:

            st.subheader(
                "Investment vs Current Value"
            )

            chart_df = pd.DataFrame(
                {
                    "Type": [
                        "Investment",
                        "Current Value"
                    ],
                    "Value": [
                        total_investment,
                        current_value
                    ]
                }
            )

            fig = px.bar(
                chart_df,
                x="Type",
                y="Value",
                text_auto=".2s"
            )

            fig.update_layout(
                height=350,
                showlegend=False,
                yaxis_title="Value (₹)",
                xaxis_title=""
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # --------------------------------------------------------
        # Holdings
        # --------------------------------------------------------

        with right:

            st.subheader(
                "Portfolio Holdings"
            )

            st.dataframe(
                portfolio,
                use_container_width=True,
                hide_index=True
            )


    # ============================================================
    # 2. ANALYTICS
    # ============================================================

    elif section == "📊 Analytics":

        st.header("📊 Portfolio Analytics")


        # --------------------------------------------------------
        # Portfolio Summary
        # --------------------------------------------------------

        try:

            summary = calculate_portfolio_summary(
                portfolio
            )

        except Exception:

            summary = {}


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Total Value",
                f"₹ {summary.get('total_value', current_value):,.2f}"
            )


        with col2:

            st.metric(
                "Profit / Loss",
                f"₹ {summary.get('profit_loss', profit_loss):,.2f}"
            )


        with col3:

            risk_score = summary.get(
                "risk_score",
                0
            )

            st.metric(
                "Risk Score",
                f"{risk_score:.1f} / 10"
            )


        st.divider()


        # ========================================================
        # SECTOR + DAILY MOVERS
        # ========================================================

        left, right = st.columns(2)


        # --------------------------------------------------------
        # Sector Allocation
        # --------------------------------------------------------

        with left:

            st.subheader("🥧 Sector Allocation")

            try:

                sector_data = compute_sector_breakdown(
                    portfolio
                )

            except Exception:

                sector_data = {}


            if sector_data:

                sector_df = pd.DataFrame(
                    [
                        {
                            "Sector": sector,
                            "Value": data.get(
                                "value",
                                0
                            ),
                            "Portfolio %": data.get(
                                "pct_of_portfolio",
                                0
                            )
                        }

                        for sector, data
                        in sector_data.items()
                    ]
                )


                fig = px.pie(
                    sector_df,
                    names="Sector",
                    values="Value",
                    hole=0.5
                )


                fig.update_layout(
                    height=350
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "Sector information unavailable."
                )


        # --------------------------------------------------------
        # Daily Movers
        # --------------------------------------------------------

        with right:

            st.subheader("📈 Daily Movers")


            if "Change %" in portfolio.columns:

                mover_df = portfolio[
                    [
                        "Stock Symbol",
                        "Change %"
                    ]
                ].copy()


                mover_df = mover_df.sort_values(
                    "Change %",
                    ascending=False
                )


                fig = px.bar(
                    mover_df,
                    x="Stock Symbol",
                    y="Change %",
                    text_auto=".2f"
                )


                fig.update_layout(
                    height=350,
                    xaxis_title="",
                    yaxis_title="Change %"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "Daily change data unavailable."
                )


        # ========================================================
        # STOCK-WISE PROFIT / LOSS
        # ========================================================

        st.subheader(
            "💹 Stock-wise Profit / Loss"
        )


        required_pnl_columns = [
            "Stock Symbol",
            "Average Price",
            "Current Price",
            "Quantity"
        ]


        if all(
            column in portfolio.columns
            for column in required_pnl_columns
        ):

            pnl_df = portfolio[
                required_pnl_columns
            ].copy()


            pnl_df["Investment"] = (
                pnl_df["Average Price"]
                * pnl_df["Quantity"]
            )


            pnl_df["Current Value"] = (
                pnl_df["Current Price"]
                * pnl_df["Quantity"]
            )


            pnl_df["Profit / Loss"] = (
                pnl_df["Current Value"]
                - pnl_df["Investment"]
            )


            fig = px.bar(
                pnl_df,
                x="Stock Symbol",
                y="Profit / Loss",
                text_auto=".2f"
            )


            fig.update_layout(
                height=400,
                xaxis_title="",
                yaxis_title="P&L (₹)"
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Required columns for P&L analysis are unavailable."
            )

        # ============================================================
        # 3. BENCHMARK
        # ============================================================

        elif section == "🎯 Benchmark":

            st.header("🎯 Benchmark Comparison")

            # --------------------------------------------------------
            # Nifty 50 Benchmark Data
            # --------------------------------------------------------

            benchmark_data = get_market_data(["^NSEI"])

            benchmark_change = (
                benchmark_data
                .get("^NSEI", {})
                .get("change_pct")
            )

            if benchmark_change is not None:

                st.metric(
                    "Nifty 50 Daily Change",
                    f"{benchmark_change:+.2f}%"
                )

            else:

                st.warning(
                    "Nifty 50 benchmark data is currently unavailable."
                )


        st.markdown(
            """
            Your existing `benchmark_comparison.py` expects:

            - Portfolio analytics
            - Benchmark change %
            - Benchmark symbol

            Once the benchmark market-data service is connected,
            this section can display portfolio vs Nifty 50 performance.
            """
        )


    # ============================================================
    # 4. AI INSIGHTS
    # ============================================================

    elif section == "🤖 AI Insights":

        st.header("🤖 AI Portfolio Insights")

        st.caption(
            "AI analysis is generated from your portfolio data."
        )


        # --------------------------------------------------------
        # Health Score
        # --------------------------------------------------------

        with st.expander(
            "🩺 Portfolio Health Score",
            expanded=True
        ):

            st.write(
                "Generate an AI-based health assessment."
            )


            if st.button(
                "Generate Health Score",
                key="health_score"
            ):

                try:

                    from AI.health_score import (
                        portfolio_health_score
                    )


                    with st.spinner(
                        "Analyzing portfolio health..."
                    ):

                        result = portfolio_health_score(
                            portfolio
                        )


                    st.markdown(result)


                except Exception as e:

                    st.error(
                        f"Health analysis failed: {e}"
                    )


        # --------------------------------------------------------
        # Risk Analysis
        # --------------------------------------------------------

        with st.expander(
            "⚠️ AI Risk Analysis"
        ):

            if st.button(
                "Generate Risk Analysis",
                key="risk_analysis"
            ):

                try:

                    from AI.risk_analysis import (
                        portfolio_risk_analysis
                    )


                    with st.spinner(
                        "Analyzing portfolio risk..."
                    ):

                        result = portfolio_risk_analysis(
                            portfolio
                        )


                    st.markdown(result)


                except Exception as e:

                    st.error(
                        f"Risk analysis failed: {e}"
                    )


        # --------------------------------------------------------
        # Portfolio Summary
        # --------------------------------------------------------

        with st.expander(
            "📋 AI Portfolio Summary"
        ):

            if st.button(
                "Generate Summary",
                key="portfolio_summary"
            ):

                try:

                    from AI.portfolio_summary import (
                        generate_portfolio_summary
                    )


                    with st.spinner(
                        "Generating portfolio summary..."
                    ):

                        result = generate_portfolio_summary(
                            portfolio
                        )


                    st.markdown(result)


                except Exception as e:

                    st.error(
                        f"Summary generation failed: {e}"
                    )


        # --------------------------------------------------------
        # Improvement Suggestions
        # --------------------------------------------------------

        with st.expander(
            "💡 Improvement Suggestions"
        ):

            if st.button(
                "Generate Suggestions",
                key="improvement"
            ):

                try:

                    from AI.improvement import (
                        portfolio_improvement_suggestions
                    )


                    with st.spinner(
                        "Generating suggestions..."
                    ):

                        result = (
                            portfolio_improvement_suggestions(
                                portfolio
                            )
                        )


                    st.markdown(result)


                except Exception as e:

                    st.error(
                        f"Suggestion generation failed: {e}"
                    )


    # ============================================================
    # 5. STOCK ANALYSIS
    # ============================================================

    elif section == "📈 Stock Analysis":

        st.header("📈 Stock Analysis")


        if "Stock Symbol" not in portfolio.columns:

            st.error(
                "Stock Symbol column is not available in portfolio."
            )

            st.stop()


        stocks = (
            portfolio["Stock Symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )


        if not stocks:

            st.warning(
                "No stock symbols found."
            )

            st.stop()


        selected_stock = st.selectbox(
            "Select Stock",
            stocks
        )


        # --------------------------------------------------------
        # Get Stock Info
        # --------------------------------------------------------

        with st.spinner(
            "Loading stock information..."
        ):

            try:

                stock_info = get_stock_info(
                    selected_stock
                )

            except Exception as e:

                stock_info = {}

                st.warning(
                    f"Unable to load stock information: {e}"
                )


        # --------------------------------------------------------
        # Stock KPI
        # --------------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)


        with col1:

            current_price_info = stock_info.get(
                "Current Price"
            )

            st.metric(
                "Current Price",
                (
                    f"₹ {current_price_info:,.2f}"
                    if isinstance(
                        current_price_info,
                        (int, float)
                    )
                    else "N/A"
                )
            )


        with col2:

            st.metric(
                "P/E Ratio",
                stock_info.get(
                    "PE Ratio",
                    "N/A"
                )
            )


        with col3:

            st.metric(
                "52W High",
                stock_info.get(
                    "52 Week High",
                    "N/A"
                )
            )


        with col4:

            st.metric(
                "52W Low",
                stock_info.get(
                    "52 Week Low",
                    "N/A"
                )
            )


        st.divider()


        # --------------------------------------------------------
        # Company Information + Portfolio Position
        # --------------------------------------------------------

        left, right = st.columns(2)


        with left:

            st.subheader(
                "🏢 Company Information"
            )


            st.write(
                f"**Company:** "
                f"{stock_info.get('Company name', 'N/A')}"
            )


            st.write(
                f"**Sector:** "
                f"{stock_info.get('sector', 'N/A')}"
            )


            st.write(
                f"**Industry:** "
                f"{stock_info.get('Industry', 'N/A')}"
            )


            st.write(
                f"**Market Cap:** "
                f"{stock_info.get('Market Cap', 'N/A')}"
            )


        with right:

            st.subheader(
                "📊 Portfolio Position"
            )


            selected_df = portfolio[
                portfolio["Stock Symbol"]
                .astype(str)
                .str.strip()
                == selected_stock
            ]


            st.dataframe(
                selected_df,
                use_container_width=True,
                hide_index=True
            )


        # --------------------------------------------------------
        # AI Stock Explanation
        # --------------------------------------------------------

        st.subheader(
            "🤖 AI Stock Explanation"
        )


        if st.button(
            "Generate AI Stock Analysis",
            key="stock_ai"
        ):

            try:

                from AI.stock_explainer import (
                    explain_stock
                )


                company_text = str(
                    stock_info
                )


                with st.spinner(
                    "Analyzing stock..."
                ):

                    result = explain_stock(
                        company_text
                    )


                st.markdown(result)


            except Exception as e:

                st.error(
                    f"Stock analysis failed: {e}"
                )


    # ============================================================
    # 6. MARKET NEWS
    # ============================================================

    elif section == "📰 Market News":

        st.header("📰 Latest Market News")


        if "Stock Symbol" not in portfolio.columns:

            st.error(
                "Stock Symbol column is not available in portfolio."
            )

            st.stop()


        stocks = (
            portfolio["Stock Symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )


        if not stocks:

            st.warning(
                "No stock symbols found."
            )

            st.stop()


        selected_stock = st.selectbox(
            "Select Stock",
            stocks,
            key="news_stock"
        )


        if st.button(
            "🔄 Fetch Latest News",
            key="fetch_news"
        ):

            with st.spinner(
                "Fetching latest news..."
            ):

                try:

                    articles = get_stock_news(
                        selected_stock
                    )


                    st.session_state.news_data[
                        selected_stock
                    ] = articles


                except Exception as e:

                    st.error(
                        f"News fetching failed: {e}"
                    )


        articles = st.session_state.news_data.get(
            selected_stock,
            []
        )


        if not articles:

            st.info(
                "Click 'Fetch Latest News' to load news."
            )


        else:

            for article in articles:

                title = article.get(
                    "Title",
                    article.get(
                        "title",
                        ""
                    )
                )


                description = article.get(
                    "Description",
                    article.get(
                        "description",
                        ""
                    )
                )


                source = article.get(
                    "source",
                    ""
                )


                published = article.get(
                    "published",
                    ""
                )


                url = article.get(
                    "url",
                    ""
                )


                with st.container(border=True):

                    if title:

                        st.markdown(
                            f"### 📰 {title}"
                        )


                    if description:

                        st.write(
                            description
                        )


                    meta = []


                    if source:

                        meta.append(
                            f"Source: {source}"
                        )


                    if published:

                        meta.append(
                            f"Published: {published}"
                        )


                    if meta:

                        st.caption(
                            " • ".join(meta)
                        )


                    if url:

                        st.link_button(
                            "Read Full Article",
                            url
                        )


    # ============================================================
    # 7. ASK AI
    # ============================================================

    elif section == "💬 Ask AI":

        st.header("💬 Ask AI")


        st.caption(
            "Ask questions about your portfolio, "
            "stocks and available market news."
        )


        question = st.text_area(
            "Your Question",
            placeholder=(
                "Example: Which stock is contributing "
                "the most to my portfolio risk?"
            ),
            height=120
        )


        if st.button(
            "🤖 Ask AI",
            type="primary",
            use_container_width=True
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


                    # ------------------------------------------------
                    # Convert news keys to AI format
                    # ------------------------------------------------

                    ai_news_data = {}


                    for stock, articles in (
                        st.session_state.news_data.items()
                    ):

                        ai_news_data[stock] = []


                        for article in articles:

                            ai_news_data[stock].append(
                                {
                                    "title": article.get(
                                        "Title",
                                        article.get(
                                            "title",
                                            ""
                                        )
                                    ),

                                    "description": article.get(
                                        "Description",
                                        article.get(
                                            "description",
                                            ""
                                        )
                                    ),

                                    "source": article.get(
                                        "source",
                                        ""
                                    ),

                                    "published": article.get(
                                        "published",
                                        ""
                                    )
                                }
                            )


                    with st.spinner(
                        "AI is analyzing your portfolio..."
                    ):

                        answer = portfolio_chat(
                            portfolio,
                            question,
                            ai_news_data
                        )


                    st.divider()


                    st.subheader(
                        "🤖 AI Answer"
                    )


                    st.markdown(
                        answer
                    )


                except Exception as e:

                    st.error(
                        f"AI Chat failed: {e}"
                    )
if __name__ == "__main__":
    main()