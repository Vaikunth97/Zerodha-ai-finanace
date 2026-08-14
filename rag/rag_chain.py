import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .retriever import retrieve_documents


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


# ============================================================
# OPENROUTER LLM - LAZY LOADING
# ============================================================

_llm = None


def _get_llm():
    """
    Create and cache the OpenRouter LLM client.

    Lazy loading prevents the entire FastAPI application
    from crashing during import if the API key is missing.
    """

    global _llm

    if _llm is None:

        if not OPENROUTER_API_KEY:
            raise ValueError(
                f"OPENROUTER_API_KEY not found in {ENV_FILE}"
            )

        model_name = os.getenv(
            "OPENROUTER_MODEL",
            "openai/gpt-4o-mini"
        )

        _llm = ChatOpenAI(
            model=model_name,
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
            max_tokens=650,
        )

    return _llm


# ============================================================
# RAG PROMPT
# ============================================================

RAG_PROMPT = ChatPromptTemplate.from_template(
    """
You are a financial education assistant for the
Zerodha AI Financial Intelligence project.

Answer the user's financial question using the
retrieved financial context provided below.

IMPORTANT RULES:

1. Use the retrieved context as the primary source
   for your answer.

2. If the retrieved context contains enough information
   to answer the question, answer directly.

3. Do NOT say:
   "The document does not provide a direct definition"
   if the retrieved context actually defines or explains
   the concept.

4. Do NOT mention:
   - retrieved document
   - retrieved context
   - RAG context
   - vector database
   - FAISS
   - document chunk

5. Do not invent financial facts that are unsupported
   by the supplied context.

6. If the answer genuinely cannot be found in the
   supplied context, respond exactly with:

   "I could not find this information in the provided financial documents."

7. Include formulas when they appear in the context.

8. Include examples when they are useful and supported
   by the context.

9. Keep the response concise, clear and educational.

10. Do not provide investment guarantees.

11. Respond only with the final answer.

============================================================
RETRIEVED FINANCIAL CONTEXT
============================================================

{context}

============================================================
USER QUESTION
============================================================

{question}

============================================================
FINAL ANSWER
============================================================
"""
)


# ============================================================
# BUILD CONTEXT FROM DOCUMENTS
# ============================================================

def build_context(documents):
    """
    Convert retrieved LangChain documents into a clean
    text context for the LLM.
    """

    context_parts = []

    for index, document in enumerate(
        documents,
        start=1
    ):

        source = document.metadata.get(
            "source",
            "Unknown"
        )

        page = document.metadata.get(
            "page_label",
            document.metadata.get(
                "page",
                "Unknown"
            )
        )

        text = document.page_content.strip()

        if not text:
            continue

        context_part = f"""
DOCUMENT {index}

Source:
{source}

Page:
{page}

Content:
{text}
"""

        context_parts.append(
            context_part
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# RAG FUNCTION
# ============================================================

def ask_rag(
    question: str,
    k: int = 4
) -> str:
    """
    Retrieve relevant financial information using the
    smart retriever and generate a grounded answer using
    OpenRouter.
    """

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )


    # --------------------------------------------------------
    # RETRIEVE DOCUMENTS
    # --------------------------------------------------------

    print(
        "\nSearching financial documents..."
    )

    documents = retrieve_documents(
        question,
        k=k
    )


    # --------------------------------------------------------
    # NO DOCUMENTS
    # --------------------------------------------------------

    if not documents:

        return (
            "I could not find this information in the "
            "provided financial documents."
        )


    # --------------------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------------------

    context = build_context(
        documents
    )


    if not context.strip():

        return (
            "I could not find this information in the "
            "provided financial documents."
        )


    # --------------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------------

    print(
        f"\nUsing {len(documents)} retrieved document(s)."
    )

    for index, document in enumerate(
        documents,
        start=1
    ):

        source = document.metadata.get(
            "source",
            "Unknown"
        )

        page = document.metadata.get(
            "page_label",
            document.metadata.get(
                "page",
                "Unknown"
            )
        )

        print(
            f"Document {index}: "
            f"{Path(str(source)).name} | "
            f"Page: {page}"
        )


    # --------------------------------------------------------
    # FORMAT PROMPT
    # --------------------------------------------------------

    formatted_prompt = RAG_PROMPT.format(
        context=context,
        question=question
    )


    # --------------------------------------------------------
    # CALL LLM
    # --------------------------------------------------------

    try:

        response = _get_llm().invoke(
            formatted_prompt
        )

    except Exception as error:

        print(
            f"\nLLM error: {error}"
        )

        raise


    # --------------------------------------------------------
    # VALIDATE RESPONSE
    # --------------------------------------------------------

    if response is None:

        return (
            "I could not generate an answer "
            "at this time."
        )


    answer = getattr(
        response,
        "content",
        ""
    )


    if not answer:

        return (
            "I could not generate an answer "
            "at this time."
        )


    # --------------------------------------------------------
    # NORMALIZE ANSWER
    # --------------------------------------------------------

    answer = str(
        answer
    ).strip()


    if not answer:

        return (
            "I could not generate an answer "
            "at this time."
        )


    return answer


# ============================================================
# OPTIONAL: RETURN ANSWER + SOURCES
# ============================================================

def ask_rag_with_sources(
    question: str,
    k: int = 4
):
    """
    Same RAG process but also returns source metadata.

    Useful later if you want Streamlit to display
    document citations.
    """

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )


    documents = retrieve_documents(
        question,
        k=k
    )


    if not documents:

        return {
            "answer": (
                "I could not find this information in the "
                "provided financial documents."
            ),
            "sources": []
        }


    context = build_context(
        documents
    )


    if not context.strip():

        return {
            "answer": (
                "I could not find this information in the "
                "provided financial documents."
            ),
            "sources": []
        }


    formatted_prompt = RAG_PROMPT.format(
        context=context,
        question=question
    )


    response = _get_llm().invoke(
        formatted_prompt
    )


    answer = getattr(
        response,
        "content",
        ""
    )


    answer = str(
        answer
    ).strip()


    sources = []


    for document in documents:

        source = document.metadata.get(
            "source",
            "Unknown"
        )

        page = document.metadata.get(
            "page_label",
            document.metadata.get(
                "page",
                "Unknown"
            )
        )

        sources.append(
            {
                "source": str(source),
                "page": page,
            }
        )


    return {
        "answer": answer,
        "sources": sources,
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "ZERODHA AI - RAG TEST"
    )

    print(
        "=" * 70
    )


    while True:

        try:

            question = input(
                "\nEnter your question "
                "(or type 'exit'): "
            ).strip()


            if question.lower() in {
                "exit",
                "quit",
                "q"
            }:

                print(
                    "\nExiting RAG test."
                )

                break


            if not question:

                print(
                    "\nPlease enter a question."
                )

                continue


            print(
                "\nProcessing question..."
            )


            answer = ask_rag(
                question,
                k=4
            )


            print(
                "\n"
                + "=" * 70
            )

            print(
                "RAG ANSWER"
            )

            print(
                "=" * 70
            )

            print(
                "\n"
                + answer
            )


        except KeyboardInterrupt:

            print(
                "\n\nExiting RAG test."
            )

            break


        except Exception as error:

            print(
                "\n"
                + "=" * 70
            )

            print(
                "ERROR"
            )

            print(
                "=" * 70
            )

            print(
                f"\n{error}"
            )