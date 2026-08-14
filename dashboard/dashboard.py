# ============================================================
# ZERODHA AI FINANCIAL INTELLIGENCE - STREAMLIT DASHBOARD
# ============================================================

import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf


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
# FASTAPI CONFIGURATION
# ============================================================

FASTAPI_URL = "http://127.0.0.1:8000"


# ============================================================
# FASTAPI HEALTH CHECK
# ============================================================

def check_fastapi():
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/health",
            timeout=3,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


# ============================================================
# DATAFRAME -> JSON SAFE RECORDS
# ============================================================

def prepare_portfolio_payload(portfolio_df):
    """
    Convert dataframe into JSON-safe portfolio records.
    """

    safe_df = portfolio_df.copy()

    # Convert NaN/NaT to None
    safe_df = safe_df.astype(object).where(
        pd.notnull(safe_df),
        None,
    )

    # Convert timestamps if any
    for column in safe_df.columns:
        safe_df[column] = safe_df[column].apply(
            lambda value: (
                value.isoformat()
                if isinstance(value, pd.Timestamp)
                else value
            )
        )

    return safe_df.to_dict(
        orient="records"
    )


# ============================================================
# GENERIC FASTAPI POST
# ============================================================

def post_fastapi(endpoint, payload, timeout=120):
    """
    Generic helper for FastAPI POST requests.
    """

    try:

        response = requests.post(
            f"{FASTAPI_URL}{endpoint}",
            json=payload,
            timeout=timeout,
        )

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "error": (
                "FastAPI backend is unavailable. "
                "Run `uvicorn fastapi_app:app --reload`."
            ),
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "FastAPI request timed out.",
        }

    except requests.RequestException as error:

        return {
            "success": False,
            "error": str(error),
        }


    if response.status_code != 200:

        try:
            body = response.json()

            detail = body.get(
                "detail",
                body,
            )

        except Exception:
            detail = response.text

        return {
            "success": False,
            "error": (
                f"FastAPI error "
                f"{response.status_code}: "
                f"{detail}"
            ),
        }


    try:

        return {
            "success": True,
            "data": response.json(),
        }

    except Exception:

        return {
            "success": False,
            "error": (
                "FastAPI returned an invalid JSON response."
            ),
        }


# ============================================================
# PORTFOLIO AI API
# ============================================================

def call_portfolio_ai_api(endpoint, portfolio_df):

    payload = {
        "portfolio": prepare_portfolio_payload(
            portfolio_df
        )
    }

    api_response = post_fastapi(
        endpoint,
        payload,
    )

    if not api_response["success"]:
        return api_response

    result = api_response["data"].get(
        "result"
    )

    if not result:
        return {
            "success": False,
            "error": "AI did not return a result.",
        }

    return {
        "success": True,
        "result": result,
    }


# ============================================================
# RAG API
# ============================================================

def call_rag_api(question):

    api_response = post_fastapi(
        "/api/rag/query",
        {
            "question": question
        },
    )

    if not api_response["success"]:
        return api_response

    answer = api_response["data"].get(
        "answer"
    )

    if not answer:
        return {
            "success": False,
            "error": (
                "RAG did not return an answer."
            ),
        }

    return {
        "success": True,
        "answer": answer,
    }


# ============================================================
# STOCK AI API
# ============================================================

def call_stock_ai_api(stock_data):

    api_response = post_fastapi(
        "/api/ai/stock-analysis",
        {
            "stock_data": stock_data
        },
    )

    if not api_response["success"]:
        return api_response

    result = api_response["data"].get(
        "result"
    )

    if not result:
        return {
            "success": False,
            "error": (
                "AI stock analysis returned "
                "no result."
            ),
        }

    return {
        "success": True,
        "result": result,
    }


# ============================================================
# HISTORICAL MARKET DATA
# ============================================================

def get_historical_data(
    symbols,
    period="1y",
):
    """
    Fetch historical closing prices for portfolio stocks.
    """

    historical_data = []

    for symbol in symbols:

        try:

            yahoo_symbol = f"{symbol}.NS"

            stock = yf.Ticker(
                yahoo_symbol
            )

            history = stock.history(
                period=period,
                auto_adjust=False,
            )

            if history.empty:
                continue

            history = history.reset_index()

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
                f"Historical data error "
                f"for {symbol}: {error}"
            )


    if not historical_data:

        return pd.DataFrame()


    return pd.concat(
        historical_data,
        ignore_index=True,
    )


# ============================================================
# MAIN
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
    # STYLE
    # ========================================================

    st.markdown(
        """
        <style>

        .main-title {
            font-size: 42px !important;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .main-subtitle {
            font-size: 18px !important;
            font-weight: 400;
            color: #6b6b6b;
        }

        </style>
        """,
        unsafe_allow_html=True,
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

    if "rag_answer" not in st.session_state:
        st.session_state.rag_answer = None

    if "stock_ai_result" not in st.session_state:
        st.session_state.stock_ai_result = None


    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        """
        <div class="main-title">
            📊 Zerodha AI Financial Intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="main-subtitle">
            Portfolio Analytics • Market Data •
            News • AI Insights
        </div>
        """,
        unsafe_allow_html=True,
    )


    # ========================================================
    # SIDEBAR PORTFOLIO
    # ========================================================

    with st.sidebar:

        st.header(
            "📁 Portfolio"
        )

        uploaded_file = st.file_uploader(
            "Upload Portfolio",
            type=[
                "csv",
                "xlsx",
            ],
        )

        st.divider()


        if (
            st.session_state.portfolio_data
            is not None
        ):

            st.success(
                "Portfolio loaded"
            )

            if st.session_state.file_name:

                st.caption(
                    f"File: "
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

                        df = updated_current_price(
                            df
                        )

                        st.session_state.portfolio_data = (
                            df
                        )

                    st.success(
                        "Market data updated"
                    )

                except Exception as error:

                    st.error(
                        f"Market data update "
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

                    portfolio = read_portfolio(
                        uploaded_file
                    )


                # =================================================
                # VALIDATION
                # =================================================

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


                # =================================================
                # CLEANING
                # =================================================

                portfolio = clean_data(
                    portfolio
                )


                # =================================================
                # MARKET DATA
                # =================================================

                with st.spinner(
                    "Fetching live market data..."
                ):

                    portfolio = (
                        updated_current_price(
                            portfolio
                        )
                    )


                # =================================================
                # SAVE
                # =================================================

                st.session_state.portfolio_data = (
                    portfolio
                )

                st.session_state.file_name = (
                    uploaded_file.name
                )

                st.session_state.news_data = {}

                # Clear previous AI results
                st.session_state.health_result = None
                st.session_state.risk_result = None
                st.session_state.summary_result = None
                st.session_state.improvement_result = None
                st.session_state.stock_ai_result = None


            except Exception as error:

                st.error(
                    f"Unable to process "
                    f"portfolio: {error}"
                )

                st.stop()


    # ========================================================
    # NO PORTFOLIO
    # ========================================================

    if (
        st.session_state.portfolio_data
        is None
    ):

        st.info(
            "👈 Upload your portfolio "
            "from the sidebar to begin."
        )

        st.divider()

        st.markdown(
            "## 🧭 What you can explore"
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.markdown(
                "### 📈 Portfolio Overview"
            )

            st.write(
                "Track your investments, "
                "current value and overall P&L."
            )

            st.caption(
                "Investment • Current Value • Returns"
            )


        with col2:

            st.markdown(
                "### 📊 Portfolio Analytics"
            )

            st.write(
                "Analyze sectors, gainers, "
                "losers and portfolio concentration."
            )

            st.caption(
                "Sectors • Gainers • Losers • Risk"
            )


        with col3:

            st.markdown(
                "### 🎯 Benchmark"
            )

            st.write(
                "Compare your portfolio "
                "against the Nifty 50."
            )

            st.caption(
                "Portfolio vs Nifty 50"
            )


        col4, col5, col6 = st.columns(3)


        with col4:

            st.markdown(
                "### 🤖 AI Insights"
            )

            st.write(
                "Generate AI-based portfolio "
                "health and risk insights."
            )

            st.caption(
                "Health • Risk • Suggestions"
            )


        with col5:

            st.markdown(
                "### 📰 Market News"
            )

            st.write(
                "View recent news related "
                "to portfolio holdings."
            )

            st.caption(
                "Stocks • News • Sources"
            )


        with col6:

            st.markdown(
                "### 💬 Ask AI"
            )

            st.write(
                "Ask financial education "
                "questions using RAG."
            )

            st.caption(
                "RAG • FAISS • Financial Knowledge"
            )


        st.stop()


    # ========================================================
    # DATA
    # ========================================================

    portfolio = (
        st.session_state.portfolio_data
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
    # 1. OVERVIEW
    # ========================================================

    if section == "📈 Overview":

        st.header(
            "📈 Portfolio Overview"
        )


        col1, col2, col3, col4 = (
            st.columns(4)
        )


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


        # ====================================================
        # INVESTMENT VS CURRENT VALUE
        # ====================================================

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
                        total_investment,
                        current_value,
                    ],
                }
            )


            fig = px.bar(
                chart_df,
                x="Type",
                y="Value",
                text_auto=".2s",
            )


            fig.update_layout(
                height=350,
                showlegend=False,
                yaxis_title="Value (₹)",
                xaxis_title="",
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


        # ====================================================
        # HOLDINGS
        # ====================================================

        with right:

            st.subheader(
                "Portfolio Holdings"
            )

            st.dataframe(
                portfolio,
                width="stretch",
                hide_index=True,
            )


    # ========================================================
    # 2. ANALYTICS
    # ========================================================

    elif section == "📊 Analytics":

        st.header(
            "📊 Portfolio Analytics"
        )


        try:

            summary = (
                calculate_portfolio_summary(
                    portfolio
                )
            )

        except Exception:

            summary = {}


        col1, col2, col3 = (
            st.columns(3)
        )


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

            risk_score = summary.get(
                "risk_score",
                0,
            )

            st.metric(
                "Risk Score",
                f"{risk_score:.1f} / 10",
            )


        st.divider()


        left, right = st.columns(2)


        # ====================================================
        # SECTOR ALLOCATION
        # ====================================================

        with left:

            st.subheader(
                "🥧 Sector Allocation"
            )


            try:

                sector_data = (
                    compute_sector_breakdown(
                        portfolio
                    )
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
                                0,
                            ),
                            "Portfolio %": data.get(
                                "pct_of_portfolio",
                                0,
                            ),
                        }
                        for sector, data
                        in sector_data.items()
                    ]
                )


                fig = px.pie(
                    sector_df,
                    names="Sector",
                    values="Value",
                    hole=0.5,
                )


                fig.update_layout(
                    height=350,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02,
                    ),
                )


                st.plotly_chart(
                    fig,
                    width="stretch",
                )

            else:

                st.info(
                    "Sector information unavailable."
                )


        # ====================================================
        # DAILY MOVERS
        # ====================================================

        with right:

            st.subheader(
                "📈 Daily Movers"
            )


            if (
                "Change %"
                in portfolio.columns
            ):

                mover_df = portfolio[
                    [
                        "Stock Symbol",
                        "Change %",
                    ]
                ].copy()


                mover_df = mover_df.dropna(
                    subset=["Change %"]
                )


                mover_df = (
                    mover_df.drop_duplicates(
                        subset="Stock Symbol",
                        keep="first",
                    )
                )


                mover_df = (
                    mover_df.sort_values(
                        "Change %",
                        ascending=False,
                    )
                )


                if mover_df.empty:

                    st.info(
                        "Daily change data unavailable."
                    )

                else:

                    fig = px.bar(
                        mover_df,
                        x="Stock Symbol",
                        y="Change %",
                        text_auto=".2f",
                    )


                    fig.update_layout(
                        height=350,
                        xaxis_title="",
                        yaxis_title="Change %",
                    )


                    st.plotly_chart(
                        fig,
                        width="stretch",
                    )

            else:

                st.info(
                    "Daily change data unavailable."
                )


        # ====================================================
        # GAINERS / LOSERS
        # ====================================================

        st.divider()

        st.subheader(
            "🏆 Top Gainers & Losers"
        )


        if (
            "Stock Symbol"
            in portfolio.columns
            and
            "Change %"
            in portfolio.columns
        ):

            mover_data = portfolio[
                [
                    "Stock Symbol",
                    "Change %",
                ]
            ].copy()


            mover_data = mover_data.dropna(
                subset=["Change %"]
            )


            mover_data = (
                mover_data.drop_duplicates(
                    subset="Stock Symbol",
                    keep="first",
                )
            )


            top_gainers = (
                mover_data
                .sort_values(
                    "Change %",
                    ascending=False,
                )
                .head(5)
            )


            top_losers = (
                mover_data
                .sort_values(
                    "Change %",
                    ascending=True,
                )
                .head(5)
            )


            gain_col, loss_col = (
                st.columns(2)
            )


            with gain_col:

                st.markdown(
                    "### 🟢 Top Gainers"
                )


                if not top_gainers.empty:

                    fig = px.bar(
                        top_gainers,
                        x="Stock Symbol",
                        y="Change %",
                        text_auto=".2f",
                    )


                    st.plotly_chart(
                        fig,
                        width="stretch",
                    )


            with loss_col:

                st.markdown(
                    "### 🔴 Top Losers"
                )


                if not top_losers.empty:

                    fig = px.bar(
                        top_losers,
                        x="Stock Symbol",
                        y="Change %",
                        text_auto=".2f",
                    )


                    st.plotly_chart(
                        fig,
                        width="stretch",
                    )


        # ====================================================
        # STOCK P&L
        # ====================================================

        st.divider()

        st.subheader(
            "💹 Stock-wise Profit / Loss"
        )


        required_columns = [
            "Stock Symbol",
            "Average Price",
            "Current Price",
            "Quantity",
        ]


        if all(
            column in portfolio.columns
            for column in required_columns
        ):

            pnl_df = portfolio[
                required_columns
            ].copy()


            pnl_df["Current Price"] = (
                pnl_df["Current Price"].fillna(
                    pnl_df["Average Price"]
                )
            )


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


            pnl_df = (
                pnl_df.groupby(
                    "Stock Symbol",
                    as_index=False,
                )
                .agg(
                    {
                        "Investment": "sum",
                        "Current Value": "sum",
                        "Profit / Loss": "sum",
                    }
                )
            )


            fig = px.bar(
                pnl_df,
                x="Stock Symbol",
                y="Profit / Loss",
                text_auto=".2f",
            )


            fig.update_layout(
                height=400,
                yaxis_title="P&L (₹)",
                xaxis_title="",
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


        # ====================================================
        # PORTFOLIO PERFORMANCE
        # ====================================================

        st.divider()

        st.subheader(
            "📈 Portfolio Performance Over Time"
        )


        period_option = st.selectbox(
            "Select Time Range",
            [
                "1 Month",
                "3 Months",
                "6 Months",
                "1 Year",
            ],
            key="performance_period",
        )


        period_mapping = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
        }


        if (
            "Stock Symbol"
            in portfolio.columns
        ):

            symbols = (
                portfolio["Stock Symbol"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )


            with st.spinner(
                "Loading historical "
                "portfolio data..."
            ):

                historical_df = (
                    get_historical_data(
                        symbols,
                        period_mapping[
                            period_option
                        ],
                    )
                )


            if not historical_df.empty:

                quantity_map = (
                    portfolio
                    .groupby(
                        "Stock Symbol"
                    )["Quantity"]
                    .sum()
                    .to_dict()
                )


                historical_df[
                    "Quantity"
                ] = (
                    historical_df[
                        "Stock Symbol"
                    ]
                    .map(
                        quantity_map
                    )
                    .fillna(0)
                )


                historical_df[
                    "Portfolio Value"
                ] = (
                    historical_df["Close"]
                    * historical_df["Quantity"]
                )


                performance_df = (
                    historical_df
                    .groupby(
                        "Date"
                    )["Portfolio Value"]
                    .sum()
                    .reset_index()
                )


                performance_df[
                    "Date"
                ] = (
                    pd.to_datetime(
                        performance_df["Date"]
                    )
                    .dt.tz_localize(None)
                )


                fig = px.line(
                    performance_df,
                    x="Date",
                    y="Portfolio Value",
                    title=(
                        "Portfolio Value Over Time"
                    ),
                )


                fig.update_layout(
                    height=450,
                    yaxis_title=(
                        "Portfolio Value (₹)"
                    ),
                )


                st.plotly_chart(
                    fig,
                    width="stretch",
                )


    # ========================================================
    # 3. BENCHMARK
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


        if benchmark_change is not None:

            col1, col2 = (
                st.columns(2)
            )


            with col1:

                st.metric(
                    "Portfolio Return",
                    f"{profit_loss_pct:+.2f}%",
                )


            with col2:

                st.metric(
                    "Nifty 50 Daily Change",
                    f"{benchmark_change:+.2f}%",
                )


            benchmark_df = pd.DataFrame(
                {
                    "Asset": [
                        "My Portfolio",
                        "Nifty 50",
                    ],
                    "Return (%)": [
                        profit_loss_pct,
                        benchmark_change,
                    ],
                }
            )


            fig = px.bar(
                benchmark_df,
                x="Asset",
                y="Return (%)",
                text_auto=".2f",
                title=(
                    "Portfolio vs Nifty 50"
                ),
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


        else:

            st.warning(
                "Nifty 50 benchmark data "
                "is currently unavailable."
            )


        st.divider()

        st.subheader(
            "📈 Historical Benchmark Comparison"
        )


        benchmark_period = st.selectbox(
            "Select Benchmark Period",
            [
                "1 Month",
                "3 Months",
                "6 Months",
                "1 Year",
            ],
            key="benchmark_period",
        )


        benchmark_period_mapping = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
        }


        try:

            benchmark_history = (
                yf.Ticker("^NSEI")
                .history(
                    period=(
                        benchmark_period_mapping[
                            benchmark_period
                        ]
                    ),
                    auto_adjust=False,
                )
            )


            if not benchmark_history.empty:

                benchmark_history = (
                    benchmark_history
                    .reset_index()
                )


                benchmark_history[
                    "Date"
                ] = (
                    pd.to_datetime(
                        benchmark_history[
                            "Date"
                        ]
                    )
                    .dt.tz_localize(None)
                )


                first_value = (
                    benchmark_history[
                        "Close"
                    ].iloc[0]
                )


                benchmark_history[
                    "Nifty Return %"
                ] = (
                    (
                        benchmark_history[
                            "Close"
                        ]
                        / first_value
                    )
                    - 1
                ) * 100


                fig = px.line(
                    benchmark_history,
                    x="Date",
                    y="Nifty Return %",
                    title=(
                        "Nifty 50 Performance"
                    ),
                )


                st.plotly_chart(
                    fig,
                    width="stretch",
                )


        except Exception as error:

            st.warning(
                f"Historical benchmark "
                f"data unavailable: {error}"
            )


    # ========================================================
    # 4. AI INSIGHTS
    # ========================================================

    elif section == "🤖 AI Insights":

        st.header(
            "🤖 AI Portfolio Insights"
        )

        st.caption(
            "AI portfolio analysis through "
            "the FastAPI backend."
        )


        if check_fastapi():

            st.success(
                "🟢 FastAPI AI backend connected"
            )

        else:

            st.error(
                "🔴 FastAPI backend unavailable"
            )

            st.code(
                "uvicorn fastapi_app:app --reload"
            )


        # ====================================================
        # HEALTH SCORE
        # ====================================================

        with st.expander(
            "🩺 Portfolio Health Score",
            expanded=True,
        ):

            st.write(
                "Evaluate portfolio health, "
                "performance and diversification."
            )


            if st.button(
                "Generate Health Score",
                key="health_score_button",
                width="stretch",
            ):

                with st.spinner(
                    "Analyzing portfolio health..."
                ):

                    result = call_portfolio_ai_api(
                        "/api/ai/health-score",
                        portfolio,
                    )


                if result["success"]:

                    st.session_state.health_result = (
                        result["result"]
                    )

                else:

                    st.error(
                        result["error"]
                    )


            if st.session_state.health_result:

                st.markdown(
                    st.session_state.health_result
                )


        # ====================================================
        # RISK
        # ====================================================

        with st.expander(
            "⚠️ AI Risk Analysis"
        ):

            st.write(
                "Analyze portfolio concentration "
                "and risk exposure."
            )


            if st.button(
                "Generate Risk Analysis",
                key="risk_analysis_button",
                width="stretch",
            ):

                with st.spinner(
                    "Analyzing portfolio risk..."
                ):

                    result = call_portfolio_ai_api(
                        "/api/ai/risk-analysis",
                        portfolio,
                    )


                if result["success"]:

                    st.session_state.risk_result = (
                        result["result"]
                    )

                else:

                    st.error(
                        result["error"]
                    )


            if st.session_state.risk_result:

                st.markdown(
                    st.session_state.risk_result
                )


        # ====================================================
        # SUMMARY
        # ====================================================

        with st.expander(
            "📋 AI Portfolio Summary"
        ):

            if st.button(
                "Generate Summary",
                key="summary_button",
                width="stretch",
            ):

                with st.spinner(
                    "Generating summary..."
                ):

                    result = call_portfolio_ai_api(
                        "/api/ai/portfolio-summary",
                        portfolio,
                    )


                if result["success"]:

                    st.session_state.summary_result = (
                        result["result"]
                    )

                else:

                    st.error(
                        result["error"]
                    )


            if st.session_state.summary_result:

                st.markdown(
                    st.session_state.summary_result
                )


        # ====================================================
        # IMPROVEMENT
        # ====================================================

        with st.expander(
            "💡 Improvement Suggestions"
        ):

            if st.button(
                "Generate Suggestions",
                key="improvement_button",
                width="stretch",
            ):

                with st.spinner(
                    "Generating suggestions..."
                ):

                    result = call_portfolio_ai_api(
                        "/api/ai/improvement",
                        portfolio,
                    )


                if result["success"]:

                    st.session_state.improvement_result = (
                        result["result"]
                    )

                else:

                    st.error(
                        result["error"]
                    )


            if st.session_state.improvement_result:

                st.markdown(
                    st.session_state.improvement_result
                )


    # ========================================================
    # 5. STOCK ANALYSIS
    # ========================================================

    elif section == "📈 Stock Analysis":

        st.header(
            "📈 Stock Analysis"
        )


        if (
            "Stock Symbol"
            not in portfolio.columns
        ):

            st.error(
                "Stock Symbol column "
                "is not available."
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


        selected_stock = st.selectbox(
            "Select Stock",
            stocks,
        )


        # ====================================================
        # STOCK HISTORY
        # ====================================================

        st.subheader(
            "📈 Stock Price History"
        )


        chart_period = st.radio(
            "Time Range",
            [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
            horizontal=True,
            key="stock_chart_period",
        )


        period_map = {
            "1M": "1mo",
            "3M": "3mo",
            "6M": "6mo",
            "1Y": "1y",
        }


        history = get_historical_data(
            [selected_stock],
            period_map[
                chart_period
            ],
        )


        if not history.empty:

            history[
                "Date"
            ] = (
                pd.to_datetime(
                    history["Date"]
                )
                .dt.tz_localize(None)
            )


            fig = px.line(
                history,
                x="Date",
                y="Close",
                title=(
                    f"{selected_stock} "
                    f"Price History"
                ),
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


        # ====================================================
        # STOCK INFORMATION
        # ====================================================

        try:

            with st.spinner(
                "Loading stock information..."
            ):

                stock_info = (
                    get_stock_info(
                        selected_stock
                    )
                )

        except Exception as error:

            stock_info = {}

            st.warning(
                f"Unable to load stock "
                f"information: {error}"
            )


        col1, col2, col3, col4 = (
            st.columns(4)
        )


        current_price_info = (
            stock_info.get(
                "Current Price"
            )
        )


        with col1:

            st.metric(
                "Current Price",
                (
                    f"₹ {current_price_info:,.2f}"
                    if isinstance(
                        current_price_info,
                        (int, float),
                    )
                    else "N/A"
                ),
            )


        with col2:

            st.metric(
                "P/E Ratio",
                stock_info.get(
                    "PE Ratio",
                    "N/A",
                ),
            )


        with col3:

            st.metric(
                "52W High",
                stock_info.get(
                    "52 Week High",
                    "N/A",
                ),
            )


        with col4:

            st.metric(
                "52W Low",
                stock_info.get(
                    "52 Week Low",
                    "N/A",
                ),
            )


        st.divider()


        left, right = st.columns(2)


        with left:

            st.subheader(
                "🏢 Company Information"
            )

            st.write(
                "**Company:** "
                + str(
                    stock_info.get(
                        "Company name",
                        "N/A",
                    )
                )
            )

            st.write(
                "**Sector:** "
                + str(
                    stock_info.get(
                        "sector",
                        "N/A",
                    )
                )
            )

            st.write(
                "**Industry:** "
                + str(
                    stock_info.get(
                        "Industry",
                        "N/A",
                    )
                )
            )

            st.write(
                "**Market Cap:** "
                + str(
                    stock_info.get(
                        "Market Cap",
                        "N/A",
                    )
                )
            )


        with right:

            st.subheader(
                "📊 Portfolio Position"
            )


            selected_df = portfolio[
                portfolio[
                    "Stock Symbol"
                ]
                .astype(str)
                .str.strip()
                == selected_stock
            ]


            st.dataframe(
                selected_df,
                width="stretch",
                hide_index=True,
            )


        # ====================================================
        # AI STOCK ANALYSIS
        # ====================================================

        st.divider()

        st.subheader(
            "🤖 AI Stock Explanation"
        )


        if st.button(
            "Generate AI Stock Analysis",
            key="stock_ai_button",
            width="stretch",
        ):

            stock_payload = dict(
                stock_info
            )

            stock_payload[
                "symbol"
            ] = selected_stock


            with st.spinner(
                "Analyzing stock..."
            ):

                result = call_stock_ai_api(
                    stock_payload
                )


            if result["success"]:

                st.session_state.stock_ai_result = (
                    result["result"]
                )

            else:

                st.error(
                    result["error"]
                )


        if st.session_state.stock_ai_result:

            st.markdown(
                st.session_state.stock_ai_result
            )


    # ========================================================
    # 6. MARKET NEWS
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


        selected_stock = st.selectbox(
            "Select Stock",
            stocks,
            key="news_stock",
        )


        if st.button(
            "🔄 Fetch Latest News",
            key="fetch_news",
            width="stretch",
        ):

            try:

                with st.spinner(
                    "Fetching latest news..."
                ):

                    articles = get_stock_news(
                        selected_stock
                    )


                st.session_state.news_data[
                    selected_stock
                ] = articles

            except Exception as error:

                st.error(
                    f"News fetching failed: "
                    f"{error}"
                )


        articles = (
            st.session_state
            .news_data
            .get(
                selected_stock,
                [],
            )
        )


        if not articles:

            st.info(
                "Click 'Fetch Latest News' "
                "to load news."
            )


        else:

            for article in articles:

                title = article.get(
                    "Title",
                    article.get(
                        "title",
                        "",
                    ),
                )

                description = article.get(
                    "Description",
                    article.get(
                        "description",
                        "",
                    ),
                )

                source = article.get(
                    "source",
                    "",
                )

                published = article.get(
                    "published",
                    "",
                )

                url = article.get(
                    "url",
                    "",
                )


                with st.container(
                    border=True
                ):

                    if title:

                        st.markdown(
                            f"### 📰 {title}"
                        )


                    if description:

                        st.write(
                            description
                        )


                    metadata = []

                    if source:
                        metadata.append(
                            f"Source: {source}"
                        )

                    if published:
                        metadata.append(
                            f"Published: {published}"
                        )


                    if metadata:

                        st.caption(
                            " • ".join(
                                metadata
                            )
                        )


                    if url:

                        st.link_button(
                            "Read Full Article",
                            url,
                            width="content",
                        )


    # ========================================================
    # 7. ASK AI
    # ========================================================

    elif section == "💬 Ask AI":

        st.header(
            "💬 Ask AI"
        )

        st.caption(
            "Ask financial education questions "
            "using the FastAPI RAG knowledge base."
        )


        if check_fastapi():

            st.success(
                "🟢 FastAPI RAG backend connected"
            )

        else:

            st.error(
                "🔴 FastAPI backend unavailable"
            )

            st.code(
                "uvicorn fastapi_app:app --reload"
            )


        question = st.text_area(
            "Your Question",
            placeholder=(
                "Examples:\n"
                "What is P/E ratio?\n"
                "What is diversification?\n"
                "What is expected return "
                "of a portfolio?"
            ),
            height=130,
        )


        if st.button(
            "🤖 Ask AI",
            type="primary",
            key="rag_ask_button",
            width="stretch",
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                with st.spinner(
                    "Searching financial documents..."
                ):

                    result = call_rag_api(
                        question
                    )


                if result["success"]:

                    st.session_state.rag_answer = (
                        result["answer"]
                    )

                else:

                    st.error(
                        result["error"]
                    )


        if st.session_state.rag_answer:

            st.divider()

            st.subheader(
                "🤖 AI Answer"
            )

            st.markdown(
                st.session_state.rag_answer
            )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    main()