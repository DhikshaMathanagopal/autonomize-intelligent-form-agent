import streamlit as st
import tempfile
import json
from reader import load_document_text, _donut_answer, _donut_extract_form_data, HAS_DONUT
from extractor import extract_fields
from summarizer import summarize_doc
from rag_indexer import build_index, retrieve_context
from qa_agent import answer_with_rag
from config import can_use_openai, OPENAI_API_KEY, PINECONE_API_KEY, GOOGLE_CREDS

# -----------------------------------
# Page setup
# -----------------------------------
st.set_page_config(
    page_title="Intelligent Form Agent | Autonomize AI",
    layout="wide",
)

# -----------------------------------
# Header
# -----------------------------------
st.markdown(
    """
    <style>
        .main {background-color: #F9FAFB;}
        .stTabs [role="tablist"] button {
            font-size: 16px;
            font-weight: 600;
            color: #444;
        }
        .stTabs [role="tablist"] button[data-baseweb="tab"]:hover {
            background-color: #F0F2F6;
        }
        .stSuccess {
            background-color: #E8F5E9 !important;
        }
        .stInfo {
            background-color: #E3F2FD !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Intelligent Form Agent (Hybrid Cloud + Local)")
st.caption("Autonomize-style document agent • OCR → Fields → RAG → QA → Visual Reasoning → Summary")

# -----------------------------------
# Tabs
# -----------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "Single Form QA",
        "Summarize Form",
        "Multi-Form Insights",
    ]
)

# ==================================================
# TAB 1 — SINGLE FORM QA (Hybrid OCR + Donut + RAG)
# ==================================================
with tab1:
    st.markdown("### Ask Questions from a Single Form")
    f = st.file_uploader("Upload your form", type=["pdf", "png", "jpg"])
    q = st.text_input("Enter your question")

    if st.button("Analyze") and f and q:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(f.read())
            doc_id, text = load_document_text(tmp.name)

        # --- Donut Vision Reasoning: Extract checkbox/visual data FIRST ---
        enhanced_text = text
        visual_answer = ""
        donut_data = {}
        
        if HAS_DONUT:
            with st.spinner("Extracting checkbox and visual form data (Donut)..."):
                # Extract structured checkbox data and add to text for RAG
                donut_data = _donut_extract_form_data(tmp.name)
                if donut_data:
                    # Convert Donut extracted data to text format for RAG
                    donut_text = "\n\n=== VISUAL/CHECKBOX DATA (Donut Extraction) ===\n"
                    donut_text += json.dumps(donut_data, indent=2)
                    enhanced_text = text + "\n\n" + donut_text
                    
            with st.spinner("Performing vision-language reasoning (Donut)..."):
                visual_answer = _donut_answer(tmp.name, q)
                if visual_answer:
                    st.info(f"**Donut visual answer:** {visual_answer}")

        # --- RAG-based QA (now includes checkbox data in context) ---
        with st.spinner("Retrieving relevant context and generating response..."):
            build_index([{"doc_id": doc_id, "text": enhanced_text}])  # Use enhanced text with checkbox data
            ctx = retrieve_context(q)
            ans = answer_with_rag(q, ctx)

        # --- Combine: Prioritize Donut answer for checkbox/visual questions ---
        checkbox_keywords = ["checkbox", "marked", "checked", "selected", "urgent", "routine", "option"]
        is_checkbox_question = any(kw in q.lower() for kw in checkbox_keywords)
        
        if visual_answer and (is_checkbox_question or visual_answer.lower() not in ans.lower()):
            final_answer = f"{visual_answer} (verified via visual reasoning)"
        else:
            final_answer = ans

        st.success(final_answer)

# ==================================================
# TAB 2 — SUMMARIZATION
# ==================================================
with tab2:
    st.markdown("### Generate a Smart Summary of Any Form")
    f2 = st.file_uploader("Upload form for summarization", type=["pdf", "png", "jpg"], key="summary")

    if st.button("Summarize") and f2:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(f2.read())
            doc_id, text = load_document_text(tmp.name)

        with st.spinner("Extracting structured fields..."):
            fields = extract_fields(text)
            st.json(fields)

        with st.spinner("Generating summary..."):
            summary = summarize_doc(fields, text)
            st.write(summary)

# ==================================================
# TAB 3 — MULTI-FORM QA
# ==================================================
with tab3:
    st.markdown("### Compare or Analyze Multiple Forms Together")
    files = st.file_uploader(
        "Upload multiple forms", type=["pdf", "png", "jpg"], accept_multiple_files=True
    )
    q2 = st.text_input("Enter your cross-form question")

    if st.button("Get Insights") and files and q2:
        docs = []
        
        for f3 in files:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(f3.read())
                doc_id, text = load_document_text(tmp.name)
                
                # Enhance text with Donut checkbox/visual data
                enhanced_text = text
                if HAS_DONUT:
                    donut_data = _donut_extract_form_data(tmp.name)
                    if donut_data:
                        donut_text = "\n\n=== VISUAL/CHECKBOX DATA (Donut Extraction) ===\n"
                        donut_text += json.dumps(donut_data, indent=2)
                        enhanced_text = text + "\n\n" + donut_text
                
                docs.append({"doc_id": doc_id, "text": enhanced_text})

        with st.spinner("Building knowledge base and retrieving answers..."):
            build_index(docs)
            ctx = retrieve_context(q2)
            final_ans = answer_with_rag(q2, ctx)
        st.success(final_ans)

# -----------------------------------
# Footer
# -----------------------------------
st.markdown(
    """
    <hr style="margin-top: 2em; margin-bottom: 1em;">
    <p style="text-align: center; color: #888;">
        Built with Streamlit, LangChain, and Hugging Face Donut • Autonomize AI © 2025
    </p>
    """,
    unsafe_allow_html=True,
)
