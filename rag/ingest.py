from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFDirectoryLoader,
    TextLoader,
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = BASE_DIR / "documents"

VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    print("\nLoading PDF documents...")

    # --------------------------------------------------------
    # PDF FILES
    # --------------------------------------------------------

    pdf_loader = PyPDFDirectoryLoader(
        str(DOCUMENTS_DIR)
    )

    try:
        pdf_documents = pdf_loader.load()

        documents.extend(
            pdf_documents
        )

        print(
            f"PDF pages loaded: "
            f"{len(pdf_documents)}"
        )

    except Exception as error:

        print(
            f"PDF loading error: {error}"
        )


    # --------------------------------------------------------
    # TXT FILES
    # --------------------------------------------------------

    print("\nLoading TXT documents...")

    txt_files = list(
        DOCUMENTS_DIR.glob("*.txt")
    )

    txt_count = 0

    for txt_file in txt_files:

        try:

            loader = TextLoader(
                str(txt_file),
                encoding="utf-8",
            )

            txt_documents = loader.load()

            documents.extend(
                txt_documents
            )

            txt_count += len(
                txt_documents
            )

            print(
                f"Loaded TXT: "
                f"{txt_file.name}"
            )

        except Exception as error:

            print(
                f"TXT loading error "
                f"{txt_file.name}: "
                f"{error}"
            )


    print(
        f"\nTXT documents loaded: "
        f"{txt_count}"
    )

    print(
        f"Total documents loaded: "
        f"{len(documents)}"
    )

    return documents


# ============================================================
# SPLIT DOCUMENTS
# ============================================================

def split_documents(
    documents
):

    print(
        "\nSplitting documents into chunks..."
    )

    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
        )
    )

    chunks = (
        text_splitter.split_documents(
            documents
        )
    )

    print(
        f"Total chunks created: "
        f"{len(chunks)}"
    )

    return chunks


# ============================================================
# CREATE VECTORSTORE
# ============================================================

def create_vectorstore(
    chunks
):

    if not chunks:

        raise ValueError(
            "No document chunks available "
            "for ingestion."
        )


    print(
        "\nLoading embedding model..."
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print(
        "Embedding model loaded."
    )


    print(
        "\nCreating FAISS vector database..."
    )

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings,
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    vectorstore.save_local(
        str(VECTORSTORE_DIR)
    )


    print(
        "\n"
        + "=" * 60
    )

    print(
        "FAISS VECTOR DATABASE "
        "CREATED SUCCESSFULLY"
    )

    print(
        "=" * 60
    )

    print(
        "\nSaved at:"
    )

    print(
        VECTORSTORE_DIR
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "ZERODHA AI - RAG INGESTION"
    )

    print(
        "=" * 60
    )


    if not DOCUMENTS_DIR.exists():

        raise FileNotFoundError(
            "Documents directory does not exist: "
            f"{DOCUMENTS_DIR}"
        )


    documents = load_documents()


    if not documents:

        raise ValueError(
            "No documents found inside "
            f"{DOCUMENTS_DIR}"
        )


    chunks = split_documents(
        documents
    )


    create_vectorstore(
        chunks
    )


    print(
        "\nRAG ingestion completed."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()