from pathlib import Path
from functools import lru_cache
import re

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# RETRIEVAL SETTINGS
# ============================================================

DEFAULT_K = 4

# Number of semantic candidates used during normal retrieval
SEMANTIC_CANDIDATES = 15

# Minimum useful chunk size
MIN_CONTENT_LENGTH = 180


# ============================================================
# LOAD VECTORSTORE
# ============================================================

@lru_cache(maxsize=1)
def load_vectorstore():

    if not VECTORSTORE_DIR.exists():

        raise FileNotFoundError(
            f"No FAISS vectorstore found at "
            f"{VECTORSTORE_DIR}. "
            "Run `python -m rag.ingest` first."
        )

    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print("Loading FAISS vector database...")

    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CONCEPT DETECTION
# ============================================================

def detect_concept(question):

    q = normalize_text(question)

    # --------------------------------------------------------
    # P/E = PRICE TO EARNINGS
    # --------------------------------------------------------

    pe_patterns = [

        r"\bp\s*/\s*e\b",

        r"\bp\s*-\s*e\b",

        r"\bpe\s+ratio\b",

        r"\bprice\s+to\s+earnings\b",

        r"\bprice[-\s]+to[-\s]+earnings\b",

        r"\bprice\s+earnings\s+ratio\b",

        r"\bprice[-\s]+earnings\s+ratio\b",

        r"\bprice\s+earnings\b",

        r"\bearnings\s+multiple\b",

        r"\bprice\s+multiple\b",

    ]

    for pattern in pe_patterns:

        if re.search(
            pattern,
            q
        ):
            return "PE"

    return None


# ============================================================
# GENUINE P/E DETECTION
# ============================================================

def is_genuine_pe_content(text):

    text = normalize_text(text)

    if not text:
        return False

    # --------------------------------------------------------
    # Exact P/E terminology
    # --------------------------------------------------------

    strong_patterns = [

        r"\bprice\s+to\s+earnings\b",

        r"\bprice[-\s]+to[-\s]+earnings\b",

        r"\bp\s*/\s*e\b",

        r"\bp\s*-\s*e\b",

        r"\bpe\s+ratio\b",

        r"\bprice\s+earnings\s+ratio\b",

        r"\bprice[-\s]+earnings\s+ratio\b",

    ]

    for pattern in strong_patterns:

        if re.search(
            pattern,
            text
        ):
            return True

    return False


# ============================================================
# P/E SCORING
# ============================================================

def pe_score(text):

    text = normalize_text(text)

    score = 0

    # --------------------------------------------------------
    # VERY STRONG EXACT MATCHES
    # --------------------------------------------------------

    if re.search(
        r"\bprice\s+to\s+earnings\b",
        text
    ):
        score += 10000

    if re.search(
        r"\bprice[-\s]+to[-\s]+earnings\b",
        text
    ):
        score += 10000

    if re.search(
        r"\bp\s*/\s*e\b",
        text
    ):
        score += 10000

    if re.search(
        r"\bp\s*-\s*e\b",
        text
    ):
        score += 9000

    if re.search(
        r"\bpe\s+ratio\b",
        text
    ):
        score += 10000

    if re.search(
        r"\bprice\s+earnings\s+ratio\b",
        text
    ):
        score += 10000

    if re.search(
        r"\bprice[-\s]+earnings\s+ratio\b",
        text
    ):
        score += 10000

    # --------------------------------------------------------
    # SUPPORTING TERMS
    # --------------------------------------------------------

    if "earnings per share" in text:
        score += 500

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT score generic:
    # "earnings"
    # "stock price"
    # "valuation"
    #
    # These create false P/E matches.
    # --------------------------------------------------------

    return score


# ============================================================
# TABLE OF CONTENTS / HEADING DETECTION
# ============================================================

def is_toc_or_heading(text):

    text = normalize_text(text)

    if not text:
        return True

    # --------------------------------------------------------
    # Very short chunks
    # --------------------------------------------------------

    if len(text) < MIN_CONTENT_LENGTH:
        return True

    words = text.split()

    # --------------------------------------------------------
    # Mostly page numbers / numbering
    # --------------------------------------------------------

    if len(words) <= 20:

        numeric_count = sum(
            1
            for word in words
            if re.fullmatch(
                r"[\d.]+",
                word
            )
        )

        if numeric_count >= len(words) * 0.5:
            return True

    # --------------------------------------------------------
    # Common TOC patterns
    # --------------------------------------------------------

    toc_patterns = [

        r"^contents$",

        r"^table of contents$",

        r"^chapter\s+\d+$",

        r"^chapter\s+\d+\s*$",

        r"^\d+\s*$",

        r"^\d+\.\d+\s*$",

    ]

    for pattern in toc_patterns:

        if re.fullmatch(
            pattern,
            text
        ):
            return True

    return False


# ============================================================
# LOW INFORMATION FILTER
# ============================================================

def is_low_information(text):

    text = normalize_text(text)

    if not text:
        return True

    # --------------------------------------------------------
    # Minimum size
    # --------------------------------------------------------

    if len(text) < MIN_CONTENT_LENGTH:
        return True

    # --------------------------------------------------------
    # Minimum word count
    # --------------------------------------------------------

    if len(text.split()) < 30:
        return True

    # --------------------------------------------------------
    # TOC / heading
    # --------------------------------------------------------

    if is_toc_or_heading(text):
        return True

    # --------------------------------------------------------
    # Detect chunks containing excessive numbers
    # --------------------------------------------------------

    words = text.split()

    if len(words) > 20:

        numeric_words = sum(
            1
            for word in words
            if re.fullmatch(
                r"[\d,.%₹$Rs\-]+",
                word
            )
        )

        numeric_ratio = (
            numeric_words /
            len(words)
        )

        if numeric_ratio > 0.45:
            return True

    return False


# ============================================================
# DOCUMENT DEDUPLICATION
# ============================================================

def deduplicate_documents(documents):

    unique_documents = []

    seen = set()

    for doc in documents:

        content = normalize_text(
            doc.page_content
        )

        identity = content[:500]

        if identity in seen:
            continue

        seen.add(identity)

        unique_documents.append(doc)

    return unique_documents


# ============================================================
# NORMAL SEMANTIC RETRIEVAL
# ============================================================

def normal_semantic_retrieval(
    question,
    k=DEFAULT_K
):

    vectorstore = load_vectorstore()

    candidate_k = max(
        SEMANTIC_CANDIDATES,
        k * 3
    )

    print(
        f"Searching semantic candidates..."
    )

    results = (
        vectorstore.similarity_search_with_score(
            question,
            k=candidate_k
        )
    )

    print(
        f"Semantic retrieval returned "
        f"{len(results)} candidates."
    )

    # --------------------------------------------------------
    # Filter low-quality chunks
    # --------------------------------------------------------

    good_documents = []

    for doc, distance in results:

        if is_low_information(
            doc.page_content
        ):
            continue

        good_documents.append(
            doc
        )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    good_documents = (
        deduplicate_documents(
            good_documents
        )
    )

    print(
        f"After quality filtering: "
        f"{len(good_documents)} candidates."
    )

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if not good_documents:

        print(
            "Quality filtering removed all "
            "candidates."
        )

        original_documents = [
            doc
            for doc, distance in results
        ]

        return (
            deduplicate_documents(
                original_documents
            )[:k]
        )

    return good_documents[:k]


# ============================================================
# P/E PRECISION RETRIEVAL
# ============================================================

def pe_precision_retrieval(
    question,
    k=DEFAULT_K
):

    vectorstore = load_vectorstore()

    print(
        "Using P/E precision retrieval..."
    )

    total_chunks = len(
        vectorstore.docstore._dict
    )

    print(
        f"Searching {total_chunks} indexed chunks..."
    )

    # --------------------------------------------------------
    # Semantic search
    #
    # Used as a supporting signal / fallback.
    # --------------------------------------------------------

    semantic_results = (
        vectorstore.similarity_search_with_score(
            question,
            k=min(
                50,
                total_chunks
            )
        )
    )

    print(
        f"Semantic retrieval returned "
        f"{len(semantic_results)} candidates."
    )

    # --------------------------------------------------------
    # FULL INDEX VERIFICATION
    #
    # This prevents:
    #
    # PE = Private Equity
    #
    # from being confused with:
    #
    # P/E = Price-to-Earnings
    # --------------------------------------------------------

    print(
        "Running full-index P/E verification..."
    )

    all_documents = list(
        vectorstore.docstore._dict.values()
    )

    genuine_pe_documents = []

    for doc in all_documents:

        text = doc.page_content

        # Only accept genuine P/E terminology
        if not is_genuine_pe_content(
            text
        ):
            continue

        score = pe_score(
            text
        )

        if score <= 0:
            continue

        genuine_pe_documents.append(
            (
                score,
                doc
            )
        )

    print(
        f"Found {len(genuine_pe_documents)} "
        f"genuine P/E-related chunks."
    )

    # ========================================================
    # GENUINE P/E RESULTS FOUND
    # ========================================================

    if genuine_pe_documents:

        # ----------------------------------------------------
        # Sort by exact lexical relevance
        # ----------------------------------------------------

        genuine_pe_documents.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print(
            "\nP/E ranking completed."
        )

        # ----------------------------------------------------
        # Print ranking
        # ----------------------------------------------------

        for rank, (
            score,
            doc
        ) in enumerate(
            genuine_pe_documents[:k],
            start=1
        ):

            page = doc.metadata.get(
                "page_label",
                doc.metadata.get(
                    "page",
                    "Unknown"
                )
            )

            print(
                f"Rank {rank} | "
                f"Score: {score:.2f} | "
                f"Distance: 999.0000 | "
                f"Page: {page}"
            )

        # ----------------------------------------------------
        # RETURN ONLY TRUE P/E DOCUMENTS
        #
        # This is the key change.
        # ----------------------------------------------------

        return [
            doc
            for score, doc
            in genuine_pe_documents[:k]
        ]

    # ========================================================
    # P/E FALLBACK
    # ========================================================

    print(
        "No genuine P/E chunks found."
    )

    print(
        "Falling back to semantic retrieval..."
    )

    fallback_documents = []

    for doc, distance in semantic_results:

        if is_low_information(
            doc.page_content
        ):
            continue

        fallback_documents.append(
            doc
        )

    fallback_documents = (
        deduplicate_documents(
            fallback_documents
        )
    )

    return fallback_documents[:k]


# ============================================================
# MAIN SMART RETRIEVER
# ============================================================

def retrieve_documents(
    question,
    k=DEFAULT_K
):

    question = question.strip()

    if not question:

        return []

    concept = detect_concept(
        question
    )

    print(
        f"\nDetected concept: {concept}"
    )

    # --------------------------------------------------------
    # P/E QUERY
    # --------------------------------------------------------

    if concept == "PE":

        return pe_precision_retrieval(
            question,
            k=k
        )

    # --------------------------------------------------------
    # NORMAL QUERY
    # --------------------------------------------------------

    print(
        "Using normal semantic retrieval..."
    )

    return normal_semantic_retrieval(
        question,
        k=k
    )


# ============================================================
# LANGCHAIN RETRIEVER
# ============================================================

def get_retriever(
    k=DEFAULT_K
):

    vectorstore = load_vectorstore()

    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": k
        }
    )

    return retriever


# ============================================================
# PRINT RESULTS
# ============================================================

def print_documents(
    documents
):

    print(
        f"\nRetrieved {len(documents)} "
        f"relevant chunks:"
    )

    for i, doc in enumerate(
        documents,
        start=1
    ):

        print(
            "\n" + "=" * 70
        )

        print(
            f"DOCUMENT CHUNK {i}"
        )

        print(
            "=" * 70
        )

        print(
            "\nContent:\n"
        )

        print(
            doc.page_content[:3000]
        )

        print(
            "\nSource:"
        )

        print(
            doc.metadata.get(
                "source",
                "Unknown"
            )
        )

        print(
            "\nPage:"
        )

        print(
            doc.metadata.get(
                "page_label",
                doc.metadata.get(
                    "page",
                    "Unknown"
                )
            )
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "ZERODHA AI - RAG RETRIEVER TEST"
    )

    print(
        "=" * 70
    )

    question = input(
        "\nQuestion: "
    ).strip()

    documents = retrieve_documents(
        question,
        k=4
    )

    print_documents(
        documents
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "RETRIEVAL COMPLETE"
    )

    print(
        "=" * 70
    )