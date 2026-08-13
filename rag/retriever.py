from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# Path to the FAISS vector database
BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# Same embedding model used during ingestion
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_vectorstore():
    """Load the existing FAISS vector database."""

    if not VECTORSTORE_DIR.exists():
        raise FileNotFoundError(
            f"No FAISS vectorstore found at {VECTORSTORE_DIR}. "
            "Run `python -m rag.ingest` first to build it."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


def get_retriever(k=4):
    """Create a retriever from the FAISS vector database."""

    vectorstore = load_vectorstore()

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": k}
    )

    return retriever


if __name__ == "__main__":

    print("Loading FAISS vector database...")

    retriever = get_retriever(k=4)

    print("Retriever loaded successfully.")

    question = input("\nEnter a question: ")

    documents = retriever.invoke(question)

    print(f"\nRetrieved {len(documents)} relevant chunks:\n")

    for i, doc in enumerate(documents, start=1):

        print("=" * 70)
        print(f"DOCUMENT CHUNK {i}")
        print("=" * 70)

        print(doc.page_content[:1000])

        print("\nMetadata:")
        print(doc.metadata)