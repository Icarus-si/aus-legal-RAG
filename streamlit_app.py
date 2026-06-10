import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag.pipeline import load_and_index_pdfs, load_vectorstore, get_rag_chain, ask_question

st.set_page_config(
    page_title="Australian Legal Case Analyser",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Australian Legal Case Analyser")
st.markdown("Upload Australian court case PDFs and ask questions — answers include exact page citations.")
st.divider()

if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

with st.sidebar:
    st.header("📁 Upload Cases")
    uploaded_files = st.file_uploader(
        "Upload PDF court cases",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files and st.button("🔍 Index Cases", use_container_width=True):
        with st.spinner("Indexing cases — this may take a minute..."):
            os.makedirs("data/cases", exist_ok=True)
            saved_paths = []
            for f in uploaded_files:
                path = f"data/cases/{f.name}"
                with open(path, "wb") as out:
                    out.write(f.read())
                saved_paths.append(path)
            try:
                chunks = load_and_index_pdfs(saved_paths)
                vs = load_vectorstore()
                st.session_state.rag_chain = get_rag_chain(vs)
                st.session_state.indexed_files = [f.name for f in uploaded_files]
                st.success(f"✅ Indexed {len(saved_paths)} case(s) — {chunks} chunks")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.indexed_files:
        st.divider()
        st.markdown("**Indexed cases:**")
        for f in st.session_state.indexed_files:
            st.markdown(f"📄 {f}")

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.caption("Built by Abhay Singh Wazir · Deakin University")

# Load existing index on startup
if st.session_state.rag_chain is None and os.path.exists("faiss_index"):
    try:
        vs = load_vectorstore()
        st.session_state.rag_chain = get_rag_chain(vs)
    except:
        pass

# Chat interface
if st.session_state.rag_chain is None:
    st.info("👈 Upload a PDF court case and click 'Index Cases' to get started")
else:
    # Show chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 View sources"):
                    for s in msg["sources"]:
                        st.markdown(f"**{s['case']}** — Page {s['page']}")
                        st.caption(s['excerpt'])

    # Chat input
    question = st.chat_input("Ask a question about the cases...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analysing cases..."):
                try:
                    result = ask_question(st.session_state.rag_chain, question)
                    st.markdown(result["answer"])
                    with st.expander("📚 View sources"):
                        for s in result["sources"]:
                            st.markdown(f"**{s['case']}** — Page {s['page']}")
                            st.caption(s['excerpt'])
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"]
                    })
                except Exception as e:
                    st.error(f"Error: {e}")