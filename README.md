# Zerodha AI Financial Intelligence Platform

An AI-assisted portfolio intelligence dashboard that turns raw holdings data into plain-language summaries, risk alerts, sector breakdowns, and AI-generated recommendations. Built as a learning project inspired by the "governed AI intelligence layer" pattern used in real fintech products — deterministic analytics first, AI explains second.

> **Status:** Fresher/learning-stage project. Core analytics, multi-section dashboard, and both interfaces (Streamlit + FastAPI) are functional. Several production-grade capabilities (see [Current Scope & Scalability Roadmap](#current-scope--scalability-roadmap)) are planned as the platform scales.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Design Principle](#core-design-principle)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Features](#features)
- [Current Scope & Scalability Roadmap](#current-scope--scalability-roadmap)
- [Future Roadmap](#future-roadmap)

---

## Overview

Retail investors can see prices, gains, and losses on a portfolio screen, but they can't always tell *why* something moved or *where risk is concentrated*. This project ingests a user's portfolio (CSV/Excel), fetches live market data, runs deterministic analytics (concentration, risk score, benchmark comparison), and uses an LLM purely to **explain** those numbers and the latest news in plain language — not to invent them.

It has two interfaces sharing the same `services/`, `Analytics/`, and `AI/` layers:
- A **Streamlit dashboard** (`app.py` → `dashboard/dashboard.py`) — primary, section-based UI (Overview, Analytics, Benchmark, AI Insights, Stock Analysis, Market News, Ask AI).
- A **FastAPI backend** (`fastapi_app.py`) — REST API exposing the same analytics/AI functions for programmatic access, with numpy/pandas types safely converted to JSON-serializable output.

---

## Architecture

```
┌─────────────────┐
│   User Upload    │  CSV / XLSX portfolio file
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│   services/portfolio.py      │  Read, validate columns, clean data
└────────┬─────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   services/market.py         │  Fetch live prices via yfinance (NSE)
│                               │  Also fetches benchmark (^NSEI) data
└────────┬─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Analytics/ (Deterministic Engine)     │
│  portfolio_analytics.py  — totals, P&L,       │
│                             risk score,        │
│                             top gainers/losers │
│  risk_alerts.py          — threshold-based     │
│                             concentration/      │
│                             volatility alerts   │
│  sector_analysis.py      — sector breakdown     │
│  benchmark_comparison.py — vs Nifty 50          │
│  (NO AI calls happen here — math only)          │
└────────┬──────────────────────────────────────┘
         │  structured numbers (dict/DataFrame)
         ▼
┌─────────────────────────────────────────────┐
│              AI/ (Explanation Layer)          │
│  client.py — OpenRouter wrapper + basic        │
│              prompt/output keyword filtering    │
│  portfolio_summary.py, health_score.py,         │
│  risk_analysis.py, improvement.py,              │
│  recommendation.py, stock_explainer.py          │
│  chat.py — now also incorporates fetched         │
│            news articles into the prompt         │
│  (Each takes analytics output, asks LLM to       │
│   explain — does not recompute numbers)          │
└────────┬──────────────────────────────────────┘
         │
         ├──────────────────────────┬─────────────────────
         ▼                          ▼
┌─────────────────────┐   ┌───────────────────────────┐
│ dashboard/           │   │  fastapi_app.py             │
│ dashboard.py          │   │  REST endpoints, JSON-safe   │
│ Section-based UI,      │   │  responses, error handling   │
│ session state,          │   │  per endpoint                │
│ per-action AI triggers  │   └───────────────────────────┘
└─────────────────────┘
```

**Flow in one line:** `Upload → Clean → Fetch live prices → Compute deterministic analytics → LLM explains the analytics (+ news, for chat) → Render on dashboard / return via API`

**Why this order matters:** The AI layer never receives raw, unverified data to reason freely over — it receives *already-computed* numbers (total value, risk score, sector %) and is asked only to explain them in natural language. This limits hallucination on the factual side, with an automated verification layer planned as the next step (see [Current Scope & Scalability Roadmap](#current-scope--scalability-roadmap)).

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI (primary) | Streamlit (multi-section, session-state driven) |
| API (secondary) | FastAPI |
| Analytics | Python, pandas, NumPy |
| Market Data | yfinance (NSE tickers, incl. ^NSEI benchmark) |
| News | yfinance `Ticker.get_news()` (Yahoo Finance) |
| LLM | OpenRouter API (model: `poolside/laguna-s-2.1:free`) |
| Charts | Plotly Express |
| Config | python-dotenv / Streamlit secrets |

---

## Project Structure

```
Zerodha-ai-finanace/
├── app.py                     # Streamlit entry point
├── fastapi_app.py             # FastAPI entry point (REST API)
├── AI/
│   ├── client.py              # OpenRouter wrapper, prompt/output filtering
│   ├── portfolio_summary.py
│   ├── health_score.py
│   ├── risk_analysis.py
│   ├── improvement.py
│   ├── recommendation.py
│   ├── stock_explainer.py
│   └── chat.py                # Now also uses fetched news as context
├── Analytics/
│   ├── portfolio_analytics.py # Core deterministic engine
│   ├── risk_alerts.py         # Rule-based alerts
│   ├── sector_analysis.py
│   └── benchmark_comparison.py
├── services/
│   ├── portfolio.py           # File read/validate/clean
│   ├── market.py               # yfinance price + benchmark fetch
│   └── news.py                 # yfinance-based news fetch
└── dashboard/
    └── dashboard.py             # Streamlit UI (7 sections, session state)
```

---

## Core Design Principle

> **"Math calculates, AI only explains."**

All numeric outputs (total value, P&L, risk score, sector concentration, top gainers/losers) come from deterministic Python functions in `Analytics/`. No AI call ever computes a number — it only receives already-computed numbers (and, for chat, news headlines) and generates a natural-language explanation around them. This is the same governance pattern used in production fintech AI systems, applied at a scope appropriate for a learning project.

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd Zerodha-ai-finanace

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables (see below)
cp .env.example .env

# 5a. Run the Streamlit dashboard
streamlit run app.py

# 5b. OR run the FastAPI backend
uvicorn fastapi_app:app --reload
```

Upload a CSV/Excel file with at least these columns: `Stock Symbol`, `Quantity`, `Average Price`.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | LLM access via OpenRouter |

> News no longer depends on a separate API key — it's fetched directly via `yfinance`, so `NEWSDATA_API_KEY` is no longer required.

Secrets are read via `os.getenv()` (with `load_dotenv()`) or `st.secrets` — never hardcoded, never sent to the frontend.

---

## Features

- Portfolio upload (CSV/XLSX) with column validation, data cleaning, and **session-state persistence** (no re-upload needed on every interaction)
- Section-based dashboard: **Overview, Analytics, Benchmark, AI Insights, Stock Analysis, Market News, Ask AI**
- Manual **"Refresh Market Data"** button — live prices update only on demand, not on every rerun
- Live price fetch via yfinance (NSE), including Nifty 50 (`^NSEI`) benchmark data
- KPI dashboard: total investment, current value, P&L, P&L %
- Deterministic risk score (0–10) based on concentration + sector + volatility
- Rule-based risk alerts (top-holding concentration, sector concentration, single-day drops)
- Sector allocation table + pie chart
- Benchmark comparison vs Nifty 50
- **Top 5 gainers / top 5 losers** with dedicated charts
- AI-generated portfolio summary, health score, risk analysis, and improvement suggestions — each **triggered individually via its own button**, so AI calls only run when the user actually requests that insight
- Per-stock AI company analysis + Buy/Hold/Sell style recommendation
- Latest news per selected stock, fetched on demand via yfinance
- AI chat that now factors in **both portfolio data and fetched news** for more grounded answers
- Parallel FastAPI REST layer exposing the same capabilities, with:
  - Fixed service imports (`services`, not `service`)
  - NumPy/pandas → JSON type conversion (`_convert_numpy_types`) so analytics output serializes correctly
  - Per-endpoint error handling with meaningful HTTP status codes

---

## Current Scope & Scalability Roadmap

This release establishes the core architecture end-to-end — deterministic analytics feeding a governed AI explanation layer, exposed through both a dashboard and a REST API. That foundation was the priority for V1. The table below outlines what's built now versus what the platform is designed to grow into as usage, data volume, and compliance requirements increase — the same phased approach used when scaling real fintech products from MVP to production.

| Capability Area | Current State (V1) | Scale-Up Plan (V2+) | Why This Sequencing |
|---|---|---|---|
| **AI Output Format** | AI returns clear, readable Markdown — fast to demo and easy for a human to review. | Move to schema-validated JSON output (`summary`, `rationale`, `confidence`, `disclaimer` as distinct fields), enabling programmatic filtering, routing, and compliance review. | Structured output becomes essential once outputs need to be audited or consumed by other systems, not just displayed to one user. |
| **Output Verification** | The AI is deliberately scoped to only explain pre-computed, deterministic numbers — it never calculates figures itself. | Add an automated cross-check layer that verifies every number in the AI's response against the analytics engine output before display. | This "trust but verify" layer is the natural next step once the explanation layer is proven — the same pattern production copilots add after their core flow is validated. |
| **Data & Tool Access** | Market, news, and analytics functions are called directly within the app for a fast, simple integration. | Wrap these as named, logged, permissioned tool calls (an MCP-style registry), enabling audit trails and independent scaling of each data source. | Worth introducing once the platform needs to support multiple data providers, roles, or usage auditing — not required for a single-workflow V1. |
| **History & Personalization** | Each session is self-contained: upload, analyze, review — clean and stateless by design. | Add a persistence layer (SQLite/Postgres) to store portfolio snapshots, generated insights, and feedback, enabling trend tracking over time. | Persistence is the foundation for personalization and longitudinal insights — a natural V2 feature once the core analysis loop is validated. |
| **Interface Consistency** | Both Streamlit (dashboard) and FastAPI (REST API) expose the same core capabilities, supporting demo and integration use cases in parallel. | Extract a single shared workflow module both interfaces call into, guaranteeing identical behavior (e.g. news-aware chat) across every channel. | Natural consolidation step once both interfaces are stable and additional channels are planned. |
| **Observability** | Console-level output supports fast local development and debugging. | Move to structured logging (log levels, request IDs) suitable for dashboards and production monitoring. | Structured observability matters most once the platform serves multiple users and needs centralized monitoring. |
| **Automated Testing** | Core analytics functions are written as pure, deterministic functions — by design, straightforward to test. | Add `pytest` coverage for `Analytics/` (a natural first target) plus contract tests for AI output shape, forming a regression safety net as the codebase grows. | Testing investment scales with team size and release frequency — the deterministic design already makes this an easy next addition. |
| **Compliance Messaging** | Every AI prompt explicitly instructs the model to include an educational-use disclaimer. | Add a programmatic post-check that guarantees a disclaimer is present in every response, independent of model behavior. | Moving from "instructed" to "enforced" is the standard maturity step for any AI product heading toward regulated or public deployment. |
| **News Data Source** | Recently migrated from a third-party news API to `yfinance`'s built-in news, removing an external API-key dependency. | Add source diversification (multiple news providers) and sentiment tagging for richer market-movement context. | Already simplified for V1; multi-source aggregation is a natural enhancement once demand for richer context grows. |

**The throughline:** every V1 decision above optimizes for a clear, demonstrable, end-to-end pipeline first. The V2 items are the standard levers — structured output, verification, persistence, observability — that any AI product pulls once it moves from proof-of-concept to serving real, repeated, multi-user traffic.

---

## Future Roadmap

- [ ] Migrate AI responses to structured, schema-validated JSON output
- [ ] Add an automated faithfulness/verification layer between AI text and analytics numbers
- [ ] Add persistence for portfolio history, generated insights, and user feedback
- [ ] Unify Streamlit and FastAPI on a single shared workflow module for full feature parity
- [ ] Introduce a lightweight MCP-style tool registry for governed market/news/analytics access
- [ ] Add structured logging and monitoring dashboards for production observability
- [ ] Add `pytest` coverage across `Analytics/` and AI output contracts
- [ ] Add data-freshness indicators (last market data fetch timestamp) to the UI
- [ ] Diversify news sources and add sentiment tagging for richer market context

---

## Disclaimer

This platform is built for **educational purposes only**. It does not provide financial advice, and no output should be treated as a guarantee of returns. Always consult a registered financial advisor before making investment decisions.