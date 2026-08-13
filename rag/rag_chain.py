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

if not OPENROUTER_API_KEY:
    raise ValueError(
        f"OPENROUTER_API_KEY not found in {ENV_FILE}"
    )


# ============================================================
# OPENROUTER LLM
# ============================================================

llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.2,
)


# ============================================================
# RETRIEVER
# ============================================================

retriever = get_retriever(k=4)


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

    documents = retriever.invoke(question)

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

    response = llm.invoke(formatted_prompt)

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