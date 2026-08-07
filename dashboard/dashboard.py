# dashboard.py

import streamlit as st
import pandas as pd
import yfinance as yf

# importing functions from services
from services.portfolio import (
    read_portfolio,
    valid_coloumn,
    clean_data
)

from services.market import (
    updated_current_price,
    get_stock_info
)

from services.news import (
    get_stock_news
)

from Analytics.portfolio_analytics import calculate_portfolio_summary


from Analytics.risk_alerts import (
    get_risk_alerts
)

from Analytics.sector_analysis import(
    compute_sector_breakdown
)

from Analytics.benchmark_comparison import(
    compare_to_benchmark
)
from AI.portfolio_summary import generate_portfolio_summary
from AI.health_score import portfolio_health_score
from AI.risk_analysis import portfolio_risk_analysis
from AI.improvement import portfolio_improvement_suggestions
from AI.chat import portfolio_chat
from AI.recommendation import ai_stock_recommendation
from AI.stock_explainer import explain_stock

# -----------------------------
# Page Configuration
# -----------------------------
def main():
    st.set_page_config(
        page_title="AI Financial Intelligence",
        page_icon="📈",
        layout="wide"
    )

    st.title("📊 AI Financial Intelligence Dashboard")

    st.write("Upload your portfolio to see live stock prices and latest news.")

    # =====================================
    # Sidebar
    # =====================================

    uploaded_file = st.sidebar.file_uploader(
        "Upload Portfolio",
        type=["csv", "xlsx"]
    )

    # =====================================
    # After Upload
    # =====================================

    if uploaded_file is not None:

        # -----------------------------
        # Read Portfolio
        # -----------------------------
        portfolio = read_portfolio(uploaded_file)

        # -----------------------------
        # Validate Required Columns
        # -----------------------------
        missing = valid_coloumn(portfolio)

        if missing:
            st.error(f"Missing Columns : {missing}")
            st.stop()

        # -----------------------------
        # Clean Data
        # -----------------------------
        portfolio = clean_data(portfolio)

        # -----------------------------
        # Get Live Market Price
        # -----------------------------
        portfolio = updated_current_price(portfolio)
        #analytics
        summary = calculate_portfolio_summary(portfolio)
        # =====================================
        # KPI Section
        # =====================================

        st.subheader("Portfolio Summary")

        total_stock = len(portfolio)

        total_investment = summary["total_investment"]

        current_value = summary["total_value"]

        profit_loss = summary["profit_loss"]

        profit_loss_pct = summary["profit_loss_pct"]



        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
        "Total Stocks",
        total_stock
        )

        col2.metric(
        "Total Investment",
        f"₹ {total_investment:,.2f}"
        )

        col3.metric(
        "Current Value",
        f"₹ {current_value:,.2f}"
        )

        col4.metric(
        "Profit / Loss",
        f"₹ {profit_loss:,.2f}",
        f"{profit_loss_pct}%"
        )

        #portfolio performance
        st.subheader("Portfolio Performance")

        st.write(f"**Total Investment :** ₹ {summary['total_investment']:,.2f}")

        st.write(f"**Current Value :** ₹ {summary['total_value']:,.2f}")

        st.write(f"**Profit / Loss :** ₹ {summary['profit_loss']:,.2f}")

        st.write(f"**Return :** {summary['profit_loss_pct']} %")

        # =====================================
        # Portfolio Table
        # =====================================

        st.subheader("Portfolio")

        st.dataframe(
            portfolio,
            use_container_width=True
        )
        #Risk score

        st.subheader("Risk Score")

        st.metric(
        "Portfolio Risk Score",
        summary["risk_score"]
        )
        #Tisk alerts
        alerts = get_risk_alerts(portfolio)

        st.subheader("⚠️ Risk Alerts")

        if alerts:
            for alert in alerts:
                st.warning(alert["message"])
        else:
            st.success("No risk alerts found.")


        #sector background
        sector_data = compute_sector_breakdown(portfolio)

        st.subheader("📊 Sector Allocation")

        sector_df = pd.DataFrame.from_dict(
            sector_data,
            orient="index"
        ).reset_index()

        sector_df.rename(
            columns={"index": "Sector"},
            inplace=True
        )

        st.dataframe(
            sector_df,
            use_container_width=True
        )

        #Benchmark Comparison
        try:
            
            nifty = yf.Ticker("^NSEI")
            history = nifty.history(period="2d")
    
            current = history["Close"].iloc[-1]
            previous = history["Close"].iloc[-2]
        
            benchmark_change_pct = ((current - previous) / previous) * 100
    
            benchmark = compare_to_benchmark(portfolio, benchmark_change_pct)
    
            st.subheader("📈 Benchmark Comparison")
    
            col1, col2, col3 = st.columns(3)
    
            col1.metric(
                "Portfolio Return",
                f"{benchmark['portfolio_avg_change_pct']}%"
            )
    
            col2.metric(
                "Nifty 50 Return",
                f"{benchmark['benchmark_change_pct']}%"
            )
    
            col3.metric(
                "Outperformance",
                f"{benchmark['outperformance_pct']}%"
            )
        except Exception as e:
            st.warning(f"Benchmark data unavailable: {e}") 
            #Top Gainer
        st.subheader("Top Gainers")

        st.dataframe(
        pd.DataFrame(summary["top_gainers"]),
        use_container_width=True
        )

        #Top Loser
        st.subheader("Top Losers")

        st.dataframe(
        pd.DataFrame(summary["top_losers"]),
        use_container_width=True
        )

        #portfolio summary AI
        st.subheader("🤖 AI Portfolio Summary")
        portfolio_summary_ai = generate_portfolio_summary(portfolio)

        st.write(portfolio_summary_ai)


        #portfolio health score
        st.subheader("💚 AI Portfolio Health Score")
        health_score_ai = portfolio_health_score(portfolio)

        st.write(health_score_ai)

        #AI risk analysis
        st.subheader("⚠️ AI Risk Analysis")
        risk_analysis_ai = portfolio_risk_analysis(portfolio)

        st.write(risk_analysis_ai)

        #portfolio suggestion
        st.subheader("📈 AI Improvement Suggestions")
        improvement_ai = portfolio_improvement_suggestions(portfolio)

        st.write(improvement_ai)
        # =====================================
        # Stock Selection
        # =====================================

        st.subheader("Stock Details")

        stock = st.selectbox(
            "Select Stock",
            portfolio["Stock Symbol"]
        )

        # =====================================
        # Company Information
        # =====================================

        info = get_stock_info(stock)

        if info:

            st.markdown("### Company Information")

            c1, c2 = st.columns(2)

            with c1:

                st.write("**Company Name**")
                st.write(info.get("Company name"))

                st.write("**Sector**")
                st.write(info.get("sector"))

                st.write("**Industry**")
                st.write(info.get("Industry"))

                st.write("**Current Price**")
                st.write(info.get("Current Price"))

                st.write("**PE Ratio**")
                st.write(info.get("PE Ratio"))

            with c2:

                st.write("**Market Cap**")
                st.write(info.get("Market Cap"))

                st.write("**52 Week High**")
                st.write(info.get("52 Week High"))

                st.write("**52 Week Low**")
                st.write(info.get("52 Week Low"))

                st.write("**Dividend Yield**")
                st.write(info.get("Dividend Yield"))

                st.write("**Website**")
                st.write(info.get("Website"))

            #Ai Stock Explaination
            stock_explanation = explain_stock(info)

            st.subheader("🤖 AI Company Analysis")

            st.write(stock_explanation)


            #AI recommendation
            recommendation = ai_stock_recommendation(info)

            st.subheader("📊 AI Recommendation")

            st.write(recommendation)

        # =====================================
        # News
        # =====================================

        st.subheader("Latest News")

        news = get_stock_news(stock)

        if news:

            for article in news:

                st.link_button(
                "Read Full Article",
                article["url"]
                )

                st.write(article["Description"])

                st.write(f"**Source :** {article['source']}")

                st.write(f"**Published :** {article['published']}")

                

                st.divider()

        else:
            st.warning("No News Available.")

        #AI chatbot 
        st.subheader("💬 Ask AI")

        question = st.text_input(
        "Ask anything about your portfolio"
        )

        if st.button("Ask AI"):

            if question.strip():

                answer = portfolio_chat(
                    portfolio,
                    question
                )
            

                st.write(answer)
            else:
                    st.warning("Please enter a question.")

    else:

        st.info("Upload your portfolio to continue.")

