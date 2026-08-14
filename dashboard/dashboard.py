# ============================================================
# ZERODHA AI FINANCIAL INTELLIGENCE - STREAMLIT DASHBOARD
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf


# ============================================================
# AI - DIRECT IN-PROCESS INTEGRATION
# ============================================================

from AI.chat_chain import run_chat_chain
from AI.health_score import portfolio_health_score
from AI.risk_analysis import portfolio_risk_analysis
from AI.portfolio_summary import generate_portfolio_summary
from AI.improvement import portfolio_improvement_suggestions


# ============================================================
# SERVICES
# ============================================================

from services.portfolio import (
    read_portfolio,
    valid_coloumn,
    clean_data,
)

from services.market import (
    updated_current_price,
    get_stock_info,
    get_market_data,
)

from services.news import (
    get_stock_news,
)


# ============================================================
# ANALYTICS
# ============================================================

from Analytics.portfolio_analytics import (
    calculate_total_investment,
    calculate_current_value,
    calculate_profit_loss,
    calculate_profit_loss_percentage,
    calculate_portfolio_summary,
)

from Analytics.sector_analysis import (
    compute_sector_breakdown,
)


# ============================================================
# DATA CONVERSION HELPERS
# ============================================================

def prepare_portfolio_payload(portfolio_df):
    """Convert DataFrame into JSON-safe records for the AI chain."""

    if portfolio_df is None or portfolio_df.empty:
        return []

    safe_df = portfolio_df.copy()
    safe_df = safe_df.where(pd.notnull(safe_df), None)

    return safe_df.to_dict(orient="records")


def prepare_news_payload(news_data):
    """Normalize cached news so the hybrid AI chain can use it."""

    normalized = {}

    for stock, articles in (news_data or {}).items():
        normalized[stock] = []

        for article in articles:
            if not isinstance(article, dict):
                continue

            normalized[stock].append(
                {
                    "title": article.get(
                        "Title",
                        article.get("title", ""),
                    ),
                    "description": article.get(
                        "Description",
                        article.get("description", ""),
                    ),
                    "source": article.get("source", ""),
                    "published": article.get("published", ""),
                }
            )

    return normalized



# ============================================================
# NUMERIC / CHART HELPERS
# ============================================================

def to_numeric_series(series):
    """
    Convert portfolio values such as:
    ₹1,234.50, 1,234.50, '1234.50', None
    into numeric values safely.
    """
    cleaned = (
        series.astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace(
            {
                "": None,
                "None": None,
                "nan": None,
                "NaN": None,
            }
        )
    )

    return pd.to_numeric(
        cleaned,
        errors="coerce",
    )


def safe_plotly_chart(fig):
    """
    Render Plotly reliably across local and deployed Streamlit.
    """
    try:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )
    except TypeError:
        # Newer Streamlit versions prefer width="stretch".
        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )


# ============================================================
# HISTORICAL MARKET DATA
# ============================================================

def get_historical_data(
    symbols,
    period="1y",
):
    """
    Fetch historical closing prices.
    """

    historical_data = []

    for symbol in symbols:

        try:

            yahoo_symbol = (
                f"{symbol}.NS"
            )

            stock = yf.Ticker(
                yahoo_symbol
            )

            history = stock.history(
                period=period,
                auto_adjust=False,
            )

            if history.empty:

                continue

            history = (
                history.reset_index()
            )

            history["Stock Symbol"] = (
                symbol
            )

            history = history[
                [
                    "Date",
                    "Stock Symbol",
                    "Close",
                ]
            ]

            history = history.dropna(
                subset=["Close"]
            )

            historical_data.append(
                history
            )

        except Exception as error:

            print(
                "Historical data error "
                f"for {symbol}: {error}"
            )

    if not historical_data:

        return pd.DataFrame()

    return pd.concat(
        historical_data,
        ignore_index=True,
    )


# ============================================================
# MAIN APP
# ============================================================

def main():

    # ========================================================
    # PAGE CONFIG
    # ========================================================

    st.set_page_config(
        page_title=(
            "Zerodha AI Financial Intelligence"
        ),
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "portfolio_data" not in st.session_state:
        st.session_state.portfolio_data = None

    if "news_data" not in st.session_state:
        st.session_state.news_data = {}

    if "file_name" not in st.session_state:
        st.session_state.file_name = None

    if "health_result" not in st.session_state:
        st.session_state.health_result = None

    if "risk_result" not in st.session_state:
        st.session_state.risk_result = None

    if "summary_result" not in st.session_state:
        st.session_state.summary_result = None

    if "improvement_result" not in st.session_state:
        st.session_state.improvement_result = None

    if "stock_ai_result" not in st.session_state:
        st.session_state.stock_ai_result = None

    if "rag_answer" not in st.session_state:
        st.session_state.rag_answer = None

    if "chat_answer" not in st.session_state:
        st.session_state.chat_answer = None

    # ========================================================
    # HEADER
    # ========================================================

    st.title(
        "📊 Zerodha AI Financial Intelligence"
    )

    st.caption(
        "Portfolio Analytics • Market Data • "
        "News • AI Insights"
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
            type=["csv", "xlsx"],
        )

        st.divider()

        if (
            st.session_state
            .portfolio_data
            is not None
        ):

            st.success(
                "Portfolio loaded"
            )

            if st.session_state.file_name:

                st.caption(
                    "File: "
                    f"{st.session_state.file_name}"
                )

            if st.button(
                "🔄 Refresh Market Data",
                width="stretch",
            ):

                try:

                    with st.spinner(
                        "Updating market data..."
                    ):

                        df = (
                            st.session_state
                            .portfolio_data
                            .copy()
                        )

                        df = (
                            updated_current_price(
                                df
                            )
                        )

                        (
                            st.session_state
                            .portfolio_data
                        ) = df

                    st.success(
                        "Market data updated"
                    )

                except Exception as error:

                    st.error(
                        "Market data update "
                        f"failed: {error}"
                    )

    # ========================================================
    # LOAD PORTFOLIO
    # ========================================================

    if uploaded_file is not None:

        new_file = (
            st.session_state.file_name
            != uploaded_file.name
        )

        if new_file:

            try:

                with st.spinner(
                    "Reading portfolio..."
                ):

                    portfolio = (
                        read_portfolio(
                            uploaded_file
                        )
                    )

                missing_columns = (
                    valid_coloumn(
                        portfolio
                    )
                )

                if missing_columns:

                    st.error(
                        "Missing required columns: "
                        + ", ".join(
                            missing_columns
                        )
                    )

                    st.stop()

                portfolio = clean_data(
                    portfolio
                )

                with st.spinner(
                    "Fetching live market data..."
                ):

                    portfolio = (
                        updated_current_price(
                            portfolio
                        )
                    )

                (
                    st.session_state
                    .portfolio_data
                ) = portfolio

                st.session_state.file_name = (
                    uploaded_file.name
                )

                st.session_state.news_data = {}

                st.session_state.health_result = None
                st.session_state.risk_result = None
                st.session_state.summary_result = None
                st.session_state.improvement_result = None
                st.session_state.stock_ai_result = None
                st.session_state.rag_answer = None
                st.session_state.chat_answer = None

            except Exception as error:

                st.error(
                    "Unable to process portfolio: "
                    f"{error}"
                )

                st.stop()

    # ========================================================
    # NO PORTFOLIO
    # ========================================================

    if (
        st.session_state
        .portfolio_data
        is None
    ):

        st.info(
            "👈 Upload your portfolio "
            "from the sidebar to begin."
        )

        st.stop()

    # ========================================================
    # DATA
    # ========================================================

    portfolio = (
        st.session_state
        .portfolio_data
    )

    # ========================================================
    # COMMON CALCULATIONS
    # ========================================================

    try:

        total_investment = (
            calculate_total_investment(
                portfolio
            )
        )

    except Exception:

        total_investment = 0

    try:

        current_value = (
            calculate_current_value(
                portfolio
            )
        )

    except Exception:

        current_value = 0

    try:

        profit_loss = (
            calculate_profit_loss(
                portfolio
            )
        )

    except Exception:

        profit_loss = 0

    try:

        profit_loss_pct = (
            calculate_profit_loss_percentage(
                portfolio
            )
        )

    except Exception:

        profit_loss_pct = 0

    # ========================================================
    # NAVIGATION
    # ========================================================

    st.sidebar.divider()

    st.sidebar.subheader(
        "🧭 Sections"
    )

    section = st.sidebar.radio(
        "Go to",
        [
            "📈 Overview",
            "📊 Analytics",
            "🎯 Benchmark",
            "🤖 AI Insights",
            "📈 Stock Analysis",
            "📰 Market News",
            "💬 Ask AI",
        ],
    )

    # ========================================================
    # OVERVIEW
    # ========================================================

    if section == "📈 Overview":

        st.header(
            "📈 Portfolio Overview"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "💰 Total Investment",
                f"₹ {total_investment:,.2f}",
            )

        with col2:
            st.metric(
                "📊 Current Value",
                f"₹ {current_value:,.2f}",
            )

        with col3:
            st.metric(
                "💹 Profit / Loss",
                f"₹ {profit_loss:,.2f}",
            )

        with col4:
            st.metric(
                "📈 Return",
                f"{profit_loss_pct:.2f}%",
            )

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader(
                "Investment vs Current Value"
            )

            chart_df = pd.DataFrame(
                {
                    "Type": [
                        "Investment",
                        "Current Value",
                    ],
                    "Value": [
                        float(total_investment or 0),
                        float(current_value or 0),
                    ],
                }
            )

            fig = px.bar(
                chart_df,
                x="Type",
                y="Value",
                text="Value",
            )

            fig.update_traces(
                texttemplate="₹%{text:,.0f}",
                textposition="outside",
            )

            fig.update_layout(
                yaxis_title="Value (₹)",
                xaxis_title="",
                height=380,
            )

            safe_plotly_chart(fig)

        with right:
            st.subheader(
                "Portfolio Holdings"
            )

            st.dataframe(
                portfolio,
                use_container_width=True,
                hide_index=True,
            )


    # ========================================================
    # ANALYTICS
    # ========================================================

    elif section == "📊 Analytics":

        st.header(
            "📊 Portfolio Analytics"
        )

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
                f"₹ {summary.get('total_value', current_value):,.2f}",
            )

        with col2:
            st.metric(
                "Profit / Loss",
                f"₹ {summary.get('profit_loss', profit_loss):,.2f}",
            )

        with col3:
            st.metric(
                "Risk Score",
                f"{summary.get('risk_score', 0):.1f} / 10",
            )

        st.divider()

        chart_left, chart_right = st.columns(2)

        # ----------------------------------------------------
        # SECTOR ALLOCATION
        # ----------------------------------------------------

        with chart_left:
            st.subheader(
                "🥧 Sector Allocation"
            )

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
                            "Value": data.get("value", 0),
                        }
                        for sector, data in sector_data.items()
                    ]
                )

                sector_df["Value"] = to_numeric_series(
                    sector_df["Value"]
                ).fillna(0)

                sector_df = sector_df[
                    sector_df["Value"] > 0
                ]

                if not sector_df.empty:
                    fig = px.pie(
                        sector_df,
                        names="Sector",
                        values="Value",
                        hole=0.5,
                    )

                    fig.update_layout(
                        height=420,
                    )

                    safe_plotly_chart(fig)
                else:
                    st.info(
                        "Sector values are unavailable."
                    )
            else:
                st.info(
                    "Sector information unavailable."
                )

        # ----------------------------------------------------
        # HOLDING CURRENT VALUE
        # ----------------------------------------------------

        with chart_right:
            st.subheader(
                "📊 Holding Value Distribution"
            )

            holding_chart = portfolio.copy()

            required = {
                "Stock Symbol",
                "Current Price",
                "Quantity",
            }

            if required.issubset(
                holding_chart.columns
            ):
                holding_chart[
                    "_current_price_num"
                ] = to_numeric_series(
                    holding_chart["Current Price"]
                )

                holding_chart[
                    "_quantity_num"
                ] = to_numeric_series(
                    holding_chart["Quantity"]
                )

                holding_chart[
                    "Holding Current Value"
                ] = (
                    holding_chart[
                        "_current_price_num"
                    ].fillna(0)
                    * holding_chart[
                        "_quantity_num"
                    ].fillna(0)
                )

                holding_chart = (
                    holding_chart[
                        [
                            "Stock Symbol",
                            "Holding Current Value",
                        ]
                    ]
                    .groupby(
                        "Stock Symbol",
                        as_index=False,
                    )
                    .sum()
                    .sort_values(
                        "Holding Current Value",
                        ascending=True,
                    )
                )

                holding_chart = holding_chart[
                    holding_chart[
                        "Holding Current Value"
                    ] != 0
                ]

                if not holding_chart.empty:
                    fig = px.bar(
                        holding_chart,
                        x="Holding Current Value",
                        y="Stock Symbol",
                        orientation="h",
                        text="Holding Current Value",
                    )

                    fig.update_traces(
                        texttemplate="₹%{text:,.0f}",
                        textposition="outside",
                    )

                    fig.update_layout(
                        xaxis_title="Current Value (₹)",
                        yaxis_title="",
                        height=420,
                    )

                    safe_plotly_chart(fig)
                else:
                    st.warning(
                        "Current-price values are zero or unavailable."
                    )
            else:
                st.info(
                    "Holding value chart unavailable."
                )

        st.divider()

        # ----------------------------------------------------
        # PROFIT / LOSS BY STOCK
        # ----------------------------------------------------

        st.subheader(
            "💹 Profit / Loss by Holding"
        )

        pnl_chart = portfolio.copy()

        required = {
            "Stock Symbol",
            "Average Price",
            "Current Price",
            "Quantity",
        }

        if required.issubset(
            pnl_chart.columns
        ):
            qty = to_numeric_series(
                pnl_chart["Quantity"]
            ).fillna(0)

            avg = to_numeric_series(
                pnl_chart["Average Price"]
            ).fillna(0)

            current = to_numeric_series(
                pnl_chart["Current Price"]
            ).fillna(0)

            pnl_chart["P&L"] = (
                (current - avg) * qty
            )

            pnl_chart = (
                pnl_chart[
                    ["Stock Symbol", "P&L"]
                ]
                .groupby(
                    "Stock Symbol",
                    as_index=False,
                )
                .sum()
            )

            if not pnl_chart.empty:
                fig = px.bar(
                    pnl_chart,
                    x="Stock Symbol",
                    y="P&L",
                    text="P&L",
                )

                fig.update_traces(
                    texttemplate="₹%{text:,.0f}",
                    textposition="outside",
                )

                fig.update_layout(
                    yaxis_title="Profit / Loss (₹)",
                    xaxis_title="",
                    height=430,
                )

                safe_plotly_chart(fig)
            else:
                st.info(
                    "Profit / loss data unavailable."
                )
        else:
            st.info(
                "Profit / loss chart unavailable."
            )


    # ========================================================
    # BENCHMARK
    # ========================================================

    elif section == "🎯 Benchmark":

        st.header(
            "🎯 Benchmark Comparison"
        )

        benchmark_data = get_market_data(
            ["^NSEI"]
        )

        benchmark = benchmark_data.get(
            "^NSEI",
            {},
        )

        benchmark_change = benchmark.get(
            "change_pct"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Portfolio Return",
                f"{profit_loss_pct:+.2f}%",
            )

        with col2:
            if benchmark_change is not None:
                st.metric(
                    "Nifty 50 Daily Change",
                    f"{benchmark_change:+.2f}%",
                )
            else:
                st.metric(
                    "Nifty 50 Daily Change",
                    "Unavailable",
                )

        st.divider()

        st.subheader(
            "📈 Nifty 50 - 1 Year Trend"
        )

        try:
            nifty_history = yf.download(
                "^NSEI",
                period="1y",
                progress=False,
                auto_adjust=False,
            )

            if not nifty_history.empty:
                nifty_history = nifty_history.reset_index()

                if isinstance(
                    nifty_history.columns,
                    pd.MultiIndex,
                ):
                    nifty_history.columns = [
                        (
                            col[0]
                            if isinstance(col, tuple)
                            else col
                        )
                        for col in nifty_history.columns
                    ]

                nifty_history["Close"] = to_numeric_series(
                    nifty_history["Close"]
                )

                nifty_history = nifty_history.dropna(
                    subset=["Close"]
                )

                fig = px.line(
                    nifty_history,
                    x="Date",
                    y="Close",
                )

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Nifty 50 Close",
                    height=430,
                )

                safe_plotly_chart(fig)
            else:
                st.warning(
                    "Nifty 50 historical data unavailable."
                )

        except Exception as error:
            st.warning(
                f"Unable to load Nifty history: {error}"
            )

        if benchmark_change is not None:
            comparison_df = pd.DataFrame(
                {
                    "Metric": [
                        "Portfolio Return",
                        "Nifty 50 Daily Change",
                    ],
                    "Percentage": [
                        float(profit_loss_pct or 0),
                        float(benchmark_change or 0),
                    ],
                }
            )

            fig = px.bar(
                comparison_df,
                x="Metric",
                y="Percentage",
                text="Percentage",
            )

            fig.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside",
            )

            fig.update_layout(
                yaxis_title="Percentage (%)",
                xaxis_title="",
                height=380,
            )

            safe_plotly_chart(fig)


    # ========================================================
    # AI INSIGHTS - DIRECT AI CALLS
    # ========================================================

    elif section == "🤖 AI Insights":

        st.header(
            "🤖 AI Portfolio Insights"
        )

        st.caption(
            "AI insights are generated directly from the uploaded "
            "portfolio. No separate FastAPI process is required "
            "for the deployed Streamlit interface."
        )

        with st.expander(
            "🩺 Portfolio Health Score",
            expanded=True,
        ):
            if st.button(
                "Generate Health Score",
                key="health_score_button",
            ):
                try:
                    with st.spinner(
                        "Analyzing portfolio health..."
                    ):
                        result = portfolio_health_score(
                            portfolio
                        )

                    st.session_state.health_result = result

                except Exception as error:
                    st.error(
                        f"Health analysis failed: {error}"
                    )

            if st.session_state.health_result:
                st.markdown(
                    st.session_state.health_result
                )

        with st.expander(
            "⚠️ AI Risk Analysis"
        ):
            if st.button(
                "Generate Risk Analysis",
                key="risk_button",
            ):
                try:
                    with st.spinner(
                        "Analyzing portfolio risk..."
                    ):
                        result = portfolio_risk_analysis(
                            portfolio
                        )

                    st.session_state.risk_result = result

                except Exception as error:
                    st.error(
                        f"Risk analysis failed: {error}"
                    )

            if st.session_state.risk_result:
                st.markdown(
                    st.session_state.risk_result
                )

        with st.expander(
            "📋 AI Portfolio Summary"
        ):
            if st.button(
                "Generate Summary",
                key="summary_button",
            ):
                try:
                    with st.spinner(
                        "Generating portfolio summary..."
                    ):
                        result = generate_portfolio_summary(
                            portfolio
                        )

                    st.session_state.summary_result = result

                except Exception as error:
                    st.error(
                        f"Summary generation failed: {error}"
                    )

            if st.session_state.summary_result:
                st.markdown(
                    st.session_state.summary_result
                )

        with st.expander(
            "💡 Improvement Suggestions"
        ):
            if st.button(
                "Generate Suggestions",
                key="improvement_button",
            ):
                try:
                    with st.spinner(
                        "Generating suggestions..."
                    ):
                        result = portfolio_improvement_suggestions(
                            portfolio
                        )

                    st.session_state.improvement_result = result

                except Exception as error:
                    st.error(
                        f"Suggestion generation failed: {error}"
                    )

            if st.session_state.improvement_result:
                st.markdown(
                    st.session_state.improvement_result
                )


    # ========================================================
    # STOCK ANALYSIS
    # ========================================================

    elif section == "📈 Stock Analysis":

        st.header(
            "📈 Stock Analysis"
        )

        stocks = (
            portfolio["Stock Symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        selected_stock = st.selectbox(
            "Select Stock",
            stocks,
        )

        try:
            stock_info = get_stock_info(
                selected_stock
            )
        except Exception as error:
            stock_info = {}
            st.warning(
                f"Stock information unavailable: {error}"
            )

        metric1, metric2, metric3, metric4 = st.columns(4)

        current_price_value = stock_info.get(
            "Current Price",
            "Unavailable",
        )

        pe_value = stock_info.get(
            "PE Ratio",
            "Unavailable",
        )

        high_value = stock_info.get(
            "52 Week High",
            "Unavailable",
        )

        low_value = stock_info.get(
            "52 Week Low",
            "Unavailable",
        )

        with metric1:
            st.metric(
                "Current Price",
                (
                    f"₹ {current_price_value:,.2f}"
                    if isinstance(
                        current_price_value,
                        (int, float),
                    )
                    else str(current_price_value)
                ),
            )

        with metric2:
            st.metric(
                "P/E Ratio",
                (
                    f"{pe_value:.2f}"
                    if isinstance(
                        pe_value,
                        (int, float),
                    )
                    else str(pe_value)
                ),
            )

        with metric3:
            st.metric(
                "52 Week High",
                (
                    f"₹ {high_value:,.2f}"
                    if isinstance(
                        high_value,
                        (int, float),
                    )
                    else str(high_value)
                ),
            )

        with metric4:
            st.metric(
                "52 Week Low",
                (
                    f"₹ {low_value:,.2f}"
                    if isinstance(
                        low_value,
                        (int, float),
                    )
                    else str(low_value)
                ),
            )

        st.divider()

        st.subheader(
            f"📉 {selected_stock} - 1 Year Price History"
        )

        try:
            yahoo_symbol = (
                selected_stock
                if str(selected_stock).endswith(".NS")
                else f"{selected_stock}.NS"
            )

            historical = yf.download(
                yahoo_symbol,
                period="1y",
                progress=False,
                auto_adjust=False,
            )

            if not historical.empty:
                historical = historical.reset_index()

                if isinstance(
                    historical.columns,
                    pd.MultiIndex,
                ):
                    historical.columns = [
                        (
                            col[0]
                            if isinstance(col, tuple)
                            else col
                        )
                        for col in historical.columns
                    ]

                historical["Close"] = to_numeric_series(
                    historical["Close"]
                )

                historical = historical.dropna(
                    subset=["Close"]
                )

                fig = px.line(
                    historical,
                    x="Date",
                    y="Close",
                )

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Closing Price (₹)",
                    height=450,
                )

                safe_plotly_chart(fig)
            else:
                st.warning(
                    "Historical price data unavailable."
                )

        except Exception as error:
            st.warning(
                f"Unable to load historical price data: {error}"
            )

        with st.expander(
            "🏢 Company Details"
        ):
            st.json(
                stock_info
            )


    # ========================================================
    # MARKET NEWS
    # ========================================================

    elif section == "📰 Market News":

        st.header(
            "📰 Latest Market News"
        )

        stocks = (
            portfolio["Stock Symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        selected_stock = (
            st.selectbox(
                "Select Stock",
                stocks,
                key="news_stock",
            )
        )

        if st.button(
            "Fetch Latest News",
            key="fetch_news_button",
        ):

            try:

                articles = (
                    get_stock_news(
                        selected_stock
                    )
                )

                (
                    st.session_state
                    .news_data[
                        selected_stock
                    ]
                ) = articles

            except Exception as error:

                st.error(
                    f"News error: {error}"
                )

        articles = (
            st.session_state
            .news_data
            .get(
                selected_stock,
                [],
            )
        )

        for article in articles:

            st.markdown(
                "### "
                + article.get(
                    "Title",
                    article.get(
                        "title",
                        "News",
                    ),
                )
            )

            st.write(
                article.get(
                    "Description",
                    article.get(
                        "description",
                        "",
                    ),
                )
            )

    # ========================================================
    # ASK AI - DIRECT HYBRID CHAT
    # Portfolio + RAG + Tools + News
    # ========================================================

    elif section == "💬 Ask AI":

        st.header(
            "💬 Ask AI"
        )

        st.caption(
            "Ask questions about your uploaded portfolio, stocks "
            "and financial concepts. The assistant uses portfolio "
            "data, FAISS RAG knowledge and the project AI tools."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.success(
                "📊 Portfolio context: Available"
            )

        with col2:
            st.success(
                "📚 FAISS RAG knowledge: Enabled"
            )

        question = st.text_area(
            "Your Question",
            placeholder=(
                "Examples:\n"
                "Which stock has the highest current value?\n"
                "What is P/E ratio?\n"
                "Explain concentration risk based on my portfolio."
            ),
            height=130,
            key="hybrid_question",
        )

        if st.button(
            "🤖 Ask AI",
            type="primary",
            key="hybrid_ask_button",
            width="stretch",
        ):

            if not question.strip():
                st.warning(
                    "Please enter a question."
                )

            else:
                try:
                    portfolio_records = prepare_portfolio_payload(
                        portfolio
                    )

                    ai_news_data = prepare_news_payload(
                        st.session_state.news_data
                    )

                    with st.spinner(
                        "AI is analyzing your portfolio "
                        "and financial knowledge..."
                    ):
                        answer = run_chat_chain(
                            user_question=question.strip(),
                            portfolio_data=portfolio_records,
                            news_data=ai_news_data,
                        )

                    st.session_state.chat_answer = answer

                except Exception as error:
                    st.error(
                        f"AI Chat failed: {error}"
                    )

        if st.session_state.chat_answer:

            st.divider()

            st.subheader(
                "🤖 AI Answer"
            )

            st.markdown(
                st.session_state.chat_answer
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
