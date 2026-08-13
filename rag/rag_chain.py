import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .retriever import get_retriever


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

ENV_FILE = PROJECT_ROOT / ".env"


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(ENV_FILE)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# NOTE: We no longer raise here. Raising at import time means the
# whole FastAPI app fails to start if the key/vectorstore isn't
# ready yet, which breaks every other endpoint (dashboard, health
# score, etc.) even though they have nothing to do with RAG.
# The check now happens lazily, inside _get_llm(), only when RAG
# is actually used.


# ============================================================
# OPENROUTER LLM (lazy-loaded)
# ============================================================

_llm = None


def _get_llm():
    """
    Build (and cache) the OpenRouter LLM client on first use only.
    This avoids crashing the whole app at import time if the API
    key isn't configured yet.
    """
    global _llm

    if _llm is None:
        if not OPENROUTER_API_KEY:
            raise ValueError(
                f"OPENROUTER_API_KEY not found in {ENV_FILE}"
            )

        _llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
        )

    return _llm


# ============================================================
# RETRIEVER (lazy-loaded)
# ============================================================

_retriever = None


def _get_retriever():
    """
    Build (and cache) the FAISS retriever on first use only.
    This avoids crashing the whole app at import time if the
    vectorstore hasn't been built yet (run rag/ingest.py first).
    """
    global _retriever

    if _retriever is None:
        _retriever = get_retriever(k=4)

    return _retriever


# ============================================================
# RAG PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_template(
    """
You are a financial education assistant for the
Zerodha AI Financial Intelligence project.

Answer the user's question using ONLY the information
provided in the retrieved context.

If the answer cannot be found in the context, say:

"I could not find this information in the provided
financial documents."

Do not invent facts.

Keep the answer clear and concise.

Retrieved context:
{context}

User question:
{question}

Answer:
"""
)


# ============================================================
# RAG FUNCTION
# ============================================================

def ask_rag(question: str) -> str:
    """
    Retrieve relevant financial information from FAISS
    and generate an answer using OpenRouter.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    documents = _get_retriever().invoke(question)

    if not documents:
        return (
            "I could not find this information in the "
            "provided financial documents."
        )

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    formatted_prompt = prompt.format(
        context=context,
        question=question
    )

    response = _get_llm().invoke(formatted_prompt)

    return response.content


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("ZERODHA AI - RAG TEST")
    print("=" * 70)

    question = input("\nEnter your question: ")

    print("\nSearching financial documents...")

    answer = ask_rag(question)

    print("\n" + "=" * 70)
    print("RAG ANSWER")
    print("=" * 70)

    print(answer)