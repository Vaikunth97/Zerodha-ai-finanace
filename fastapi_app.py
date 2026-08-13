from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io
import numpy as np
import pandas as pd

# ===== Service layer =====
from services import market as market_service
from services import news as news_service
from services import portfolio as portfolio_service

# ===== Analytics layer =====
from Analytics import portfolio_analytics
from Analytics import risk_alerts
from Analytics import sector_analysis
from Analytics import benchmark_comparison

# ===== AI layer =====
from AI import chat as ai_chat
from AI import health_score as ai_health
from AI import improvement as ai_improvement
from AI import portfolio_summary as ai_summary
from AI import recommendation as ai_reco
from AI import risk_analysis as ai_risk
from AI import stock_explainer as ai_explainer

# ===== RAG layer [NEW] =====
from rag.rag_chain import ask_rag


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Zerodha AI Financial Intelligence",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MODELS
# =========================================================

class PortfolioAnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None


class BenchmarkMetrics(BaseModel):
    benchmark_symbol: str
    portfolio_avg_change_pct: float
    benchmark_change_pct: float
    outperformance_pct: float


class DashboardResponse(BaseModel):
    portfolio_summary: Dict[str, Any]
    sector_breakdown: Dict[str, Any]
    risk_alerts: List[Dict[str, Any]]
    benchmark_metrics: BenchmarkMetrics


class CompanyInfoRequest(BaseModel):
    company_info: str


class StockExplainRequest(BaseModel):
    company_info: str


class RAGQueryRequest(BaseModel):  # [NEW]
    question: str

def _convert_numpy_types(obj):
    """
    Convert NumPy/Pandas values into normal Python types
    so FastAPI/Pydantic can serialize them as JSON.
    """

    if isinstance(obj, dict):
        return {
            key: _convert_numpy_types(value)
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [
            _convert_numpy_types(value)
            for value in obj
        ]

    if isinstance(obj, tuple):
        return tuple(
            _convert_numpy_types(value)
            for value in obj
        )

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if pd.isna(obj):
        return None

    return obj
# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Zerodha AI Financial Intelligence API is running"
    }


# =========================================================
# PORTFOLIO HELPERS
# =========================================================

def _load_portfolio_df_from_upload(file: UploadFile) -> pd.DataFrame:
    try:
        contents = file.file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        uploaded_file = io.BytesIO(contents)

        # Preserve filename because portfolio_service may use
        # the extension to determine CSV/XLSX format.
        uploaded_file.name = file.filename or "uploaded_file"

        df = portfolio_service.read_portfolio(uploaded_file)

        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="No portfolio data found in the uploaded file."
            )

        # IMPORTANT:
        # Check your services/portfolio.py file.
        # If your function is named valid_column instead of
        # valid_coloumn, change it here.
        missing = portfolio_service.valid_coloumn(df)

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing)}"
            )

        df_clean = portfolio_service.clean_data(df)

        if df_clean is None or df_clean.empty:
            raise HTTPException(
                status_code=400,
                detail="Portfolio data is empty after cleaning."
            )

        return df_clean

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading portfolio file: {str(e)}"
        )


def _get_df_with_prices(file: UploadFile) -> pd.DataFrame:
    df_clean = _load_portfolio_df_from_upload(file)

    try:
        df_with_prices = market_service.updated_current_price(df_clean)

        if df_with_prices is None or df_with_prices.empty:
            raise HTTPException(
                status_code=400,
                detail="Unable to retrieve current market prices."
            )

        return df_with_prices

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating current prices: {str(e)}"
        )


def _build_dashboard_payload(
    df_with_prices: pd.DataFrame,
    benchmark_change_pct: float
) -> dict:

    try:
        summary = portfolio_analytics.calculate_portfolio_summary(
            df_with_prices
        )

        sector_breakdown = sector_analysis.compute_sector_breakdown(
            df_with_prices
        )

        alerts = risk_alerts.get_risk_alerts(
            df_with_prices
        )

        benchmark_metrics_dict = benchmark_comparison.compare_to_benchmark(
            df=df_with_prices,
            benchmark_change_pct=benchmark_change_pct,
        )

        return {
            "portfolio_summary": _convert_numpy_types(summary),
            "sector_breakdown": _convert_numpy_types(sector_breakdown),
            "risk_alerts": _convert_numpy_types(alerts),
            "benchmark_metrics": _convert_numpy_types(benchmark_metrics_dict),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard analytics error: {str(e)}"
        )


# =========================================================
# PORTFOLIO ANALYSIS
# =========================================================

@app.post(
    "/api/portfolio/upload-and-analyze",
    response_model=PortfolioAnalysisResponse
)
def upload_and_analyze_portfolio(
    file: UploadFile = File(...),
    timeframe: str = "1D",
    benchmark_change_pct: float = 0.5,
):

    df_with_prices = _get_df_with_prices(file)

    try:
        portfolio_analytics.calculate_portfolio_summary(
            df_with_prices
        )

        sector_analysis.compute_sector_breakdown(
            df_with_prices
        )

        risk_alerts.get_risk_alerts(
            df_with_prices
        )

        benchmark_comparison.compare_to_benchmark(
            df=df_with_prices,
            benchmark_change_pct=benchmark_change_pct,
        )

        filename = file.filename or "portfolio"

        job_id = f"JOB-upload-{filename}-{timeframe}"

        return PortfolioAnalysisResponse(
            job_id=job_id,
            status="completed",
            message="Portfolio uploaded and analytics completed.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio analysis error: {str(e)}"
        )


# =========================================================
# DASHBOARD
# =========================================================

@app.post(
    "/api/dashboard/from-file",
    response_model=DashboardResponse
)
def api_dashboard_from_file(
    file: UploadFile = File(...),
    timeframe: str = "1D",
    benchmark_change_pct: float = 0.5,
):

    df_with_prices = _get_df_with_prices(file)

    payload = _build_dashboard_payload(
        df_with_prices,
        benchmark_change_pct
    )

    return DashboardResponse(**payload)


# =========================================================
# NEWS
# =========================================================

@app.get("/api/news/{symbol}")
def api_get_news(symbol: str):

    try:
        symbol = symbol.upper()

        articles = news_service.get_stock_news(symbol)

        return {
            "symbol": symbol,
            "articles": articles
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"News fetch error: {str(e)}"
        )


# =========================================================
# STOCK INFORMATION
# =========================================================

@app.get("/api/stock/{symbol}")
def api_get_stock(symbol: str):

    try:
        symbol = symbol.upper()

        info = market_service.get_stock_info(symbol)

        if not info:
            raise HTTPException(
                status_code=404,
                detail="Stock info not found"
            )

        return {
            "symbol": symbol,
            "info": info
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stock info error: {str(e)}"
        )


# =========================================================
# RAG QUERY  [NEW]
# General financial education, no portfolio context needed.
# =========================================================

@app.post("/api/rag/query")
def api_rag_query(body: RAGQueryRequest):

    if not body.question or not body.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question is required."
        )

    try:
        answer = ask_rag(body.question)

        return {
            "question": body.question,
            "answer": answer
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG error: {str(e)}"
        )


# =========================================================
# AI CHAT
# =========================================================

@app.post("/api/chat")
def api_chat(
    file: UploadFile = File(...),
    question: str = "",
):

    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question is required."
        )

    df_with_prices = _get_df_with_prices(file)

    try:
        answer = ai_chat.portfolio_chat(
            df_with_prices,
            question
        )

        return {
            "question": question,
            "answer": answer
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI chat error: {str(e)}"
        )


# =========================================================
# AI HEALTH SCORE
# =========================================================

@app.post("/api/health-score")
def api_health_score(
    file: UploadFile = File(...)
):

    df_with_prices = _get_df_with_prices(file)

    try:
        report = ai_health.portfolio_health_score(
            df_with_prices
        )

        return {
            "health_score_report": report
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health score error: {str(e)}"
        )


# =========================================================
# AI IMPROVEMENT
# =========================================================

@app.post("/api/improvement")
def api_improvement(
    file: UploadFile = File(...)
):

    df_with_prices = _get_df_with_prices(file)

    try:
        suggestions = ai_improvement.portfolio_improvement_suggestions(
            df_with_prices
        )

        return {
            "improvement_suggestions": suggestions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Improvement analysis error: {str(e)}"
        )


# =========================================================
# AI PORTFOLIO SUMMARY
# =========================================================

@app.post("/api/portfolio-summary")
def api_portfolio_summary(
    file: UploadFile = File(...)
):

    df_with_prices = _get_df_with_prices(file)

    try:
        summary = ai_summary.generate_portfolio_summary(
            df_with_prices
        )

        return {
            "portfolio_summary_report": summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio summary error: {str(e)}"
        )


# =========================================================
# AI RISK ANALYSIS
# =========================================================

@app.post("/api/risk-analysis")
def api_risk_analysis(
    file: UploadFile = File(...)
):

    df_with_prices = _get_df_with_prices(file)

    try:
        analysis = ai_risk.portfolio_risk_analysis(
            df_with_prices
        )

        return {
            "risk_analysis_report": analysis
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk analysis error: {str(e)}"
        )


# =========================================================
# AI STOCK RECOMMENDATION
# =========================================================

@app.post("/api/stock-recommendation")
def api_stock_recommendation(
    body: CompanyInfoRequest
):

    if not body.company_info.strip():
        raise HTTPException(
            status_code=400,
            detail="company_info is required."
        )

    try:
        recommendation = ai_reco.ai_stock_recommendation(
            body.company_info
        )

        return {
            "recommendation_report": recommendation
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stock recommendation error: {str(e)}"
        )


# =========================================================
# AI STOCK EXPLAINER
# =========================================================

@app.post("/api/stock-explainer")
def api_stock_explainer(
    body: StockExplainRequest
):

    if not body.company_info.strip():
        raise HTTPException(
            status_code=400,
            detail="company_info is required."
        )

    try:
        explanation = ai_explainer.explain_stock(
            body.company_info
        )

        return {
            "stock_explanation": explanation
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stock explanation error: {str(e)}"
        )