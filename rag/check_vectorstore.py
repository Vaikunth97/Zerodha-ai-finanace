from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


print("=" * 80)
print("CHECKING FAISS CONTENT")
print("=" * 80)

print("\nLoading embeddings...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

print("Loading FAISS...")

vectorstore = FAISS.load_local(
    str(VECTORSTORE_DIR),
    embeddings,
    allow_dangerous_deserialization=True
)

print("FAISS loaded.")

print("\nSearching ALL indexed chunks for P/E-related text...")

found = 0

for doc_id, doc in vectorstore.docstore._dict.items():

    text = doc.page_content.lower()

    if (
        "p/e" in text
        or "price to earnings" in text
        or "price-to-earnings" in text
        or "price earnings" in text
    ):

        found += 1

        print("\n" + "=" * 80)
        print(f"MATCH {found}")
        print("=" * 80)

        print("\nCONTENT:")
        print(doc.page_content[:3000])

        print("\nSOURCE:")
        print(doc.metadata.get("source"))

        print("\nPAGE:")
        print(
            doc.metadata.get(
                "page_label",
                doc.metadata.get("page", "Unknown")
            )
        )


print("\n" + "=" * 80)
print(f"TOTAL P/E RELATED CHUNKS FOUND: {found}")
print("=" * 80)