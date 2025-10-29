import os, sys
from openai import OpenAI
from dotenv import load_dotenv
from rag_indexer import retrieve_context

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def answer_with_rag(query: str, context_docs=None):
    """
    Generate an answer using RAG (Retrieval-Augmented Generation).
    If no context_docs are provided, automatically retrieve relevant chunks.
    """
    # ✅ Auto-retrieve context if not provided
    if context_docs is None:
        context_docs = retrieve_context(query)

    # Prepare context
    if isinstance(context_docs, list):
        context_text = "\n\n".join(context_docs)
    else:
        context_text = str(context_docs)

    prompt = f"""
    You are an intelligent healthcare form QA agent.
    Use the provided context to answer accurately and clearly.

    Context:
    {context_text}

    Question:
    {query}

    Please provide a concise factual answer.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert in healthcare document QA."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
