from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

GLOBAL_INDEX = None

def build_index(docs):
    """
    Build a Chroma vector index from documents.
    Supports both:
      [("doc_id", "text")] and [{"doc_id": ..., "text": ...}]
    """
    global GLOBAL_INDEX

    # normalize input
    normalized = []
    for d in docs:
        if isinstance(d, tuple):
            normalized.append({"doc_id": d[0], "text": d[1]})
        elif isinstance(d, dict):
            normalized.append(d)
        else:
            raise TypeError(f"Unsupported doc format: {type(d)}")

    texts = [d["text"] for d in normalized]
    metadatas = [{"doc_id": d["doc_id"]} for d in normalized]

    embeddings = OpenAIEmbeddings()

    if GLOBAL_INDEX is None:
        GLOBAL_INDEX = Chroma.from_texts(texts, embeddings, metadatas=metadatas)
    else:
        new_index = Chroma.from_texts(texts, embeddings, metadatas=metadatas)
        for i, t in enumerate(texts):
            GLOBAL_INDEX._collection.add(
               ids=[metadatas[i]["doc_id"]],
               documents=[t],
               embeddings=[embeddings.embed_query(t)],
               metadatas=[metadatas[i]],
            )
    return GLOBAL_INDEX


def retrieve_context(arg1, arg2=None, k=3):
    """
    Retrieve top-k most relevant chunks.
    Supports:
      retrieve_context("query")
      retrieve_context(index, "query")
    """
    global GLOBAL_INDEX

    if isinstance(arg1, str):
        query = arg1
        index = GLOBAL_INDEX
    else:
        index = arg1
        query = arg2 or ""

    if index is None:
        raise ValueError("❌ No index available. Build index first.")

    results = index.similarity_search(query, k=k)
    return [r.page_content for r in results]
