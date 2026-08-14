# ============================================================
# ZERODHA AI FINANCIAL INTELLIGENCE - FASTAPI BACKEND
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================
# RAG
# ============================================================

from rag.rag_chain import ask_rag


# ============================================================
# AI MODULES
# ============================================================

from AI.health_score import portfolio_health_score
from AI.risk_analysis import portfolio_risk_analysis
from AI.portfolio_summary import generate_portfolio_summary
from AI.improvement import portfolio_improvement_suggestions
from AI.stock_explainer import explain_stock

# Hybrid chat
from AI.chat_chain import run_chat_chain


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Zerodha AI Financial Intelligence API",
    description=(
        "Backend API for portfolio analytics, "
        "AI insights, hybrid portfolio chat and "
        "RAG financial education."
    ),
    version="1.1.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RAGRequest(BaseModel):
    question: str


class PortfolioRequest(BaseModel):
    portfolio: List[Dict[str, Any]]


class StockAnalysisRequest(BaseModel):
    stock_data: Dict[str, Any]


class ChatRequest(BaseModel):
    question: str
    portfolio: Optional[List[Dict[str, Any]]] = None
    news: Optional[Dict[str, Any]] = None


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "Zerodha AI Financial Intelligence API",
        "version": "1.1.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def api_health():

    return {
        "status": "healthy"
    }


# ============================================================
# HYBRID ASK AI
# PORTFOLIO + RAG + TOOLS + NEWS
# ============================================================

@app.post("/api/chat")
def chat_endpoint(
    request: ChatRequest
):

    try:

        # ----------------------------------------------------
        # VALIDATE QUESTION
        # ----------------------------------------------------

        question = request.question.strip()

        if not question:

            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty.",
            )

        # ----------------------------------------------------
        # PORTFOLIO
        # ----------------------------------------------------

        portfolio_data = (
            request.portfolio
            if request.portfolio
            else []
        )

        # ----------------------------------------------------
        # NEWS
        # ----------------------------------------------------

        news_data = (
            request.news
            if request.news
            else {}
        )

        # ----------------------------------------------------
        # DEBUG OUTPUT
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("HYBRID ASK AI REQUEST")
        print("=" * 70)

        print(
            f"Question: {question}"
        )

        print(
            "Portfolio rows received: "
            f"{len(portfolio_data)}"
        )

        print(
            "News groups received: "
            f"{len(news_data)}"
        )

        # ----------------------------------------------------
        # RUN HYBRID CHAT
        # ----------------------------------------------------

        answer = run_chat_chain(
            user_question=question,
            portfolio_data=portfolio_data,
            news_data=news_data,
        )

        # ----------------------------------------------------
        # VALIDATE ANSWER
        # ----------------------------------------------------

        if not answer:

            raise HTTPException(
                status_code=500,
                detail="AI did not return an answer.",
            )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "question": question,
            "answer": answer,
            "portfolio_loaded": bool(
                portfolio_data
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Hybrid chat API error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PURE RAG QUERY
# ============================================================

@app.post("/api/rag/query")
def rag_query(
    request: RAGRequest
):

    try:

        question = request.question.strip()

        if not question:

            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty.",
            )

        answer = ask_rag(
            question
        )

        return {
            "question": question,
            "answer": answer,
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"RAG API error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PORTFOLIO HEALTH SCORE
# ============================================================

@app.post("/api/ai/health-score")
def health_score_endpoint(
    request: PortfolioRequest
):

    try:

        if not request.portfolio:

            raise HTTPException(
                status_code=400,
                detail="Portfolio cannot be empty.",
            )

        portfolio_df = pd.DataFrame(
            request.portfolio
        )

        result = portfolio_health_score(
            portfolio_df
        )

        return {
            "result": result
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Health score error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PORTFOLIO RISK ANALYSIS
# ============================================================

@app.post("/api/ai/risk-analysis")
def risk_analysis_endpoint(
    request: PortfolioRequest
):

    try:

        if not request.portfolio:

            raise HTTPException(
                status_code=400,
                detail="Portfolio cannot be empty.",
            )

        portfolio_df = pd.DataFrame(
            request.portfolio
        )

        result = portfolio_risk_analysis(
            portfolio_df
        )

        return {
            "result": result
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Risk analysis error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PORTFOLIO SUMMARY
# ============================================================

@app.post("/api/ai/portfolio-summary")
def portfolio_summary_endpoint(
    request: PortfolioRequest
):

    try:

        if not request.portfolio:

            raise HTTPException(
                status_code=400,
                detail="Portfolio cannot be empty.",
            )

        portfolio_df = pd.DataFrame(
            request.portfolio
        )

        result = generate_portfolio_summary(
            portfolio_df
        )

        return {
            "result": result
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Portfolio summary error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# PORTFOLIO IMPROVEMENT
# ============================================================

@app.post("/api/ai/improvement")
def improvement_endpoint(
    request: PortfolioRequest
):

    try:

        if not request.portfolio:

            raise HTTPException(
                status_code=400,
                detail="Portfolio cannot be empty.",
            )

        portfolio_df = pd.DataFrame(
            request.portfolio
        )

        result = portfolio_improvement_suggestions(
            portfolio_df
        )

        return {
            "result": result
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Improvement suggestion error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# STOCK AI EXPLANATION
# ============================================================

@app.post("/api/ai/stock-analysis")
def stock_analysis_endpoint(
    request: StockAnalysisRequest
):

    try:

        if not request.stock_data:

            raise HTTPException(
                status_code=400,
                detail="Stock data cannot be empty.",
            )

        stock_text = str(
            request.stock_data
        )

        result = explain_stock(
            stock_text
        )

        return {
            "result": result
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Stock analysis error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
def startup_event():

    print("=" * 70)
    print("ZERODHA AI FASTAPI BACKEND STARTED")
    print("=" * 70)

    print(
        "Swagger Docs: "
        "http://127.0.0.1:8000/docs"
    )

    print(
        "Hybrid Ask AI: "
        "POST /api/chat"
    )

    print(
        "Pure RAG: "
        "POST /api/rag/query"
    )

    print("=" * 70)