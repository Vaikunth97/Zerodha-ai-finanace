from pathlib import Path

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = BASE_DIR / "documents"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def main():
    # --------------------------------------------------
    # 1. LOAD PDF DOCUMENTS
    # --------------------------------------------------

    print("=" * 60)
    print("RAG INGESTION STARTED")
    print("=" * 60)

    print(f"\nDocuments directory:")
    print(DOCUMENTS_DIR)

    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Documents directory does not exist: {DOCUMENTS_DIR}. "
            "Create it and add your financial-education PDFs there."
        )

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    print(f"\nPDF files found: {len(pdf_files)}")

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {DOCUMENTS_DIR}"
        )

    for pdf in pdf_files:
        print(f"  - {pdf.name}")

    # --------------------------------------------------
    # 2. LOAD PDF CONTENT
    # --------------------------------------------------

    print("\nLoading PDF documents...")

    loader = PyPDFDirectoryLoader(str(DOCUMENTS_DIR))

    documents = loader.load()

    print(f"Total pages loaded: {len(documents)}")

    # --------------------------------------------------
    # 3. SPLIT DOCUMENTS INTO CHUNKS
    # --------------------------------------------------

    print("\nSplitting documents into chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Total chunks created: {len(chunks)}")

    # --------------------------------------------------
    # 4. CREATE EMBEDDINGS
    # --------------------------------------------------

    print("\nLoading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    print("Embedding model loaded.")

    # --------------------------------------------------
    # 5. CREATE FAISS VECTOR DATABASE
    # --------------------------------------------------

    print("\nCreating FAISS vector database...")

    vectorstore = FAISS.from_documents(chunks, embeddings)

    # --------------------------------------------------
    # 6. SAVE VECTOR DATABASE
    # --------------------------------------------------

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore.save_local(str(VECTORSTORE_DIR))

    print("\n" + "=" * 60)
    print("FAISS VECTOR DATABASE CREATED SUCCESSFULLY")
    print("=" * 60)

    print(f"\nSaved at:")
    print(VECTORSTORE_DIR)

    print("\nRAG ingestion completed.")


if __name__ == "__main__":
    main()