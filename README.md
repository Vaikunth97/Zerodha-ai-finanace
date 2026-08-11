# Zerodha AI Financial Intelligence Platform

An AI-assisted portfolio intelligence dashboard that turns raw holdings data into plain-language summaries, risk alerts, sector breakdowns, and AI-generated recommendations. Built as a learning project inspired by the "governed AI intelligence layer" pattern used in real fintech products — deterministic analytics first, AI explains second.

> **Status:** Fresher/learning-stage project. Core analytics and AI explanation flow are functional; several production-grade controls (see [Limitations](#limitations)) are intentionally out of scope for this version.

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
- [Limitations](#limitations)
- [How Limitations Will Be Addressed](#how-limitations-will-be-addressed)
- [Future Roadmap](#future-roadmap)

---

## Overview

Retail investors can see prices, gains, and losses on a portfolio screen, but they can't always tell *why* something moved or *where risk is concentrated*. This project ingests a user's portfolio (CSV/Excel), fetches live market data, runs deterministic analytics (concentration, risk score, benchmark comparison), and uses an LLM purely to **explain** those numbers in plain language — not to invent them.

It has two parallel interfaces:
- A **Streamlit dashboard** (`app.py` → `dashboard/dashboard.py`) — primary, fully working UI.
- A **FastAPI backend** (`fastapi_app.py`) — REST API exposing the same analytics/AI functions for programmatic access.

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
└────────┬─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Analytics/ (Deterministic Engine)     │
│  portfolio_analytics.py  — totals, P&L,       │
│                             risk score         │
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
│  recommendation.py, stock_explainer.py, chat.py │
│  (Each takes analytics output, asks LLM to      │
│   explain — does not recompute numbers)         │
└────────┬──────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   dashboard/dashboard.py     │  Streamlit UI: KPIs, charts,
│   OR fastapi_app.py          │  alerts, AI cards, chat
└───────────────────────────────┘
```

**Flow in one line:** `Upload → Clean → Fetch live prices → Compute deterministic analytics → LLM explains the analytics → Render on dashboard / return via API`

**Why this order matters:** The AI layer never receives raw, unverified data to reason freely over — it receives *already-computed* numbers (total value, risk score, sector %) and is asked only to explain them in natural language. This limits hallucination on the factual side, even though full validation isn't in place yet (see Limitations).

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI (primary) | Streamlit |
| API (secondary) | FastAPI |
| Analytics | Python, pandas |
| Market Data | yfinance (NSE tickers) |
| News | Newsdata.io API |
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
│   └── chat.py
├── Analytics/
│   ├── portfolio_analytics.py # Core deterministic engine
│   ├── risk_alerts.py         # Rule-based alerts
│   ├── sector_analysis.py
│   └── benchmark_comparison.py
├── services/
│   ├── portfolio.py           # File read/validate/clean
│   ├── market.py               # yfinance price fetch
│   └── news.py                 # Newsdata.io fetch
└── dashboard/
    └── dashboard.py             # Streamlit UI
```

---

## Core Design Principle

> **"Math calculates, AI only explains."**

All numeric outputs (total value, P&L, risk score, sector concentration) come from deterministic Python functions in `Analytics/`. No AI call ever computes a number — it only receives already-computed numbers and generates a natural-language explanation around them. This is the same governance pattern used in production fintech AI systems, applied at a scope appropriate for a learning project.

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
| `NEWSDATA_API_KEY` | Live news fetch for selected stock |

Secrets are read via `os.getenv()` or `st.secrets` — never hardcoded, never sent to the frontend.

---

## Features

- Portfolio upload (CSV/XLSX) with column validation and data cleaning
- Live price fetch via yfinance (NSE)
- KPI dashboard: total investment, current value, P&L, P&L %
- Deterministic risk score (0–10) based on concentration + sector + volatility
- Rule-based risk alerts (top-holding concentration, sector concentration, single-day drops)
- Sector allocation table + pie chart
- Benchmark comparison vs Nifty 50
- Top gainers / top losers
- AI-generated portfolio summary, health score, risk analysis, improvement suggestions
- Per-stock AI company analysis + Buy/Hold/Sell style recommendation
- Latest news per selected stock
- Free-form AI chat about the uploaded portfolio
- Parallel FastAPI REST layer exposing the same capabilities

---

## Limitations

This project intentionally scopes out several production/enterprise controls that a regulated fintech system would require, to stay realistic for a learning-stage build. Known limitations:

1. **No caching** — Streamlit re-runs the full script on every widget interaction, re-triggering all AI calls (summary, health score, risk analysis, improvement) each time, even when the portfolio hasn't changed. This is inefficient and cost-heavy.
2. **No structured AI output** — AI responses are free-text strings, not schema-validated JSON (no explicit `confidence`, `sources`, `disclaimer` fields that downstream code can check programmatically).
3. **No output validation / faithfulness check** — There's no step that verifies AI-stated numbers actually match the analytics engine's output; the two are only "loosely" connected by what's placed in the prompt.
4. **Weak prompt/output security** — `AI/client.py` uses a simple keyword blocklist (`"api key"`, `"system prompt"`, etc.), which is trivially bypassed via rephrasing and does not constitute real prompt-injection protection.
5. **No MCP / typed tool layer** — Market data, news, and analytics are called as direct Python functions rather than through a governed, logged, permissioned tool-access layer.
6. **No persistence layer** — No database exists; every upload/session is stateless. There's no history, no feedback storage, and no audit trail of what was shown to a user and when.
7. **Two independent, partially duplicated implementations** — Logic is implemented separately in the Streamlit dashboard and the FastAPI app, with no shared workflow layer, so they can drift out of sync.
8. **No automated tests** — No unit/integration tests exist for the analytics functions or AI output handling.
9. **Disclaimer is prompt-only** — "Educational purposes only" is requested via prompt text, not enforced in code, so it can be dropped by the model.

---

## How Limitations Will Be Addressed

| Limitation | Planned Fix | Approach |
|---|---|---|
| No caching | Add `@st.cache_data(ttl=...)` to all AI-calling functions | Cache keyed on portfolio hash; re-runs skip the AI call if data is unchanged |
| No structured output | Move AI functions to return a Pydantic-validated JSON schema (`summary`, `risk_note`, `confidence`, `disclaimer`) | Use OpenRouter's `response_format={"type": "json_object"}` and parse into a schema |
| No validation layer | Add a lightweight cross-check that extracts numbers from the AI response and compares them to `Analytics/portfolio_analytics.py` output | Flag/warn when AI text contains a number not present in the computed analytics |
| Weak security | Replace keyword blocklist with a small classifier-based or pattern-based guardrail node before the LLM call | Model the input-guardrail pattern used in larger support/finance systems: route rather than just block |
| No MCP/tool layer | Wrap `market.py`, `news.py`, and `Analytics/*` functions as named, logged tool calls with parameters and latency recorded | Even a simple in-process registry (function name, args, duration, success/fail) gets most of the governance benefit |
| No persistence | Add a SQLite/Postgres table for portfolio snapshots, generated insights, and user feedback | Minimal schema: `insight_id`, `portfolio_hash`, `insight_type`, `output`, `created_at` |
| Duplicated logic (Streamlit + FastAPI) | Extract a shared `workflow.py` that both entry points call into | Single source of truth for the input → analytics → AI → output pipeline |
| No tests | Add `pytest` unit tests for all `Analytics/` functions (they're deterministic and easy to test) | Start with analytics (pure functions), then add contract tests for AI output shape |
| Disclaimer not enforced | Post-process AI output: if disclaimer text is missing, append it programmatically before display | Simple string-presence check in `client.py` after the API response returns |

---

## Future Roadmap

- [ ] Add caching to eliminate redundant AI calls
- [ ] Migrate AI responses to structured JSON output
- [ ] Add a basic faithfulness/validation check between AI text and analytics numbers
- [ ] Add SQLite persistence for insight history and feedback
- [ ] Unify Streamlit and FastAPI on a shared workflow module
- [ ] Add `pytest` coverage for `Analytics/`
- [ ] Add data-freshness indicators (last market data fetch timestamp) to the UI
- [ ] Explore a lightweight MCP-style tool registry for market/news/analytics calls

---

## Disclaimer

This platform is built for **educational purposes only**. It does not provide financial advice, and no output should be treated as a guarantee of returns. Always consult a registered financial advisor before making investment decisions.