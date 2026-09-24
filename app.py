"""Streamlit entry point for AI Document Assistant."""

from __future__ import annotations

import html
import os
from pathlib import Path

import streamlit as st

from src.config import AppConfig
from src.rag.pipeline import DocumentAssistant
from src.services.export import build_transcript_markdown
from src.ui.styles import APP_CSS


st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


def initialize_state() -> None:
    defaults = {
        "workspace": None,
        "messages": [],
        "document_records": [],
        "summary_cache": {},
        "comparison_cache": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def source_payload(result) -> dict:
    return {
        "label": result.chunk.citation_label,
        "score": result.score,
        "text": result.chunk.text,
    }


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for index, source in enumerate(sources, start=1):
            excerpt = source.get("text", "")
            if len(excerpt) > 600:
                excerpt = excerpt[:600].rstrip() + "…"
            safe_label = html.escape(str(source.get("label", "Source")))
            safe_excerpt = html.escape(excerpt)
            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-title">S{index} · {safe_label}</div>
                    <div class="source-meta">Similarity: {source.get('score', 0):.3f}</div>
                    <div class="source-text">{safe_excerpt}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_header() -> None:
    st.markdown('<div class="app-kicker">Portfolio RAG Project</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">AI Document Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Upload workplace documents, ask grounded questions, search semantically, generate executive summaries, and compare files with evidence-backed answers.</div>',
        unsafe_allow_html=True,
    )


initialize_state()
render_header()

base_config = AppConfig()

with st.sidebar:
    st.header("Workspace")
    env_key = os.getenv("OPENAI_API_KEY", "")
    api_key = st.text_input(
        "OpenAI API key",
        value=env_key,
        type="password",
        help="Kept only in this Streamlit session unless you put it in your local .env file.",
    )
    model = st.selectbox(
        "Answer model",
        ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"],
        index=0,
        help="Luna is a cost-conscious default; change it for higher-quality analysis.",
    )
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "txt", "csv", "xlsx"],
        accept_multiple_files=True,
        help=f"Up to {base_config.max_file_size_mb} MB per file.",
    )

    process = st.button("Process documents", type="primary", use_container_width=True)

    if process:
        if not api_key.strip():
            st.error("Add an OpenAI API key before processing documents.")
        elif not uploaded_files:
            st.warning("Upload at least one document first.")
        else:
            config = AppConfig(text_model=model)
            try:
                workspace = DocumentAssistant(api_key=api_key.strip(), config=config)
                file_payloads = [(file.name, file.getvalue()) for file in uploaded_files]
                with st.spinner("Reading, chunking, and embedding documents…"):
                    records = workspace.index_documents(file_payloads)
                st.session_state.workspace = workspace
                st.session_state.document_records = records
                st.session_state.messages = []
                st.session_state.summary_cache = {}
                st.session_state.comparison_cache = {}
                st.success(f"Indexed {len(records)} document(s).")
            except Exception as exc:
                st.error(f"Could not process the documents: {exc}")

    workspace = st.session_state.workspace
    if workspace is not None:
        st.caption(
            f"{len(st.session_state.document_records)} documents · {workspace.index.size} searchable chunks"
        )
        if st.button("Clear workspace", use_container_width=True):
            st.session_state.workspace = None
            st.session_state.document_records = []
            st.session_state.messages = []
            st.session_state.summary_cache = {}
            st.session_state.comparison_cache = {}
            st.rerun()

    st.divider()
    st.caption("Tip: a sample handbook is included in `sample_docs/` for a quick demo.")

workspace = st.session_state.workspace
records = st.session_state.document_records

if workspace is None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 1 · Upload")
        st.write("Add PDF, DOCX, TXT, CSV, or Excel files from the sidebar.")
    with c2:
        st.markdown("### 2 · Index")
        st.write("The app extracts text, creates overlapping chunks, and embeds them for semantic retrieval.")
    with c3:
        st.markdown("### 3 · Ask")
        st.write("Questions are answered from the retrieved evidence with source labels such as [S1].")
    st.info("Add an API key and process one or more documents to activate the workspace.")
    st.stop()

chat_tab, docs_tab, summary_tab, search_tab, compare_tab = st.tabs(
    ["💬 Chat", "📚 Documents", "📝 Summaries", "🔎 Semantic Search", "↔️ Compare"]
)

with chat_tab:
    left, right = st.columns([4, 1])
    with left:
        st.subheader("Ask your documents")
        st.caption("Answers are constrained to retrieved passages from the uploaded files.")
    with right:
        if st.session_state.messages:
            if st.button("Clear chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))

    question = st.chat_input("Ask a question about the uploaded documents…")
    if question:
        prior_history = [
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.messages
        ]
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching your documents and composing an answer…"):
                try:
                    result = workspace.ask(question, history=prior_history)
                    sources = [source_payload(source) for source in result.sources]
                    st.markdown(result.text)
                    render_sources(sources)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result.text, "sources": sources}
                    )
                except Exception as exc:
                    st.error(f"The question could not be answered: {exc}")

    if st.session_state.messages:
        transcript = build_transcript_markdown(st.session_state.messages)
        st.download_button(
            "Download chat transcript",
            data=transcript,
            file_name="document_assistant_transcript.md",
            mime="text/markdown",
        )

with docs_tab:
    st.subheader("Indexed document library")
    total_size = sum(record.size_bytes for record in records)
    m1, m2, m3 = st.columns(3)
    m1.metric("Documents", len(records))
    m2.metric("Searchable chunks", workspace.index.size)
    m3.metric("Total upload size", f"{total_size / 1024:.1f} KB")

    for record in records:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
            c1.markdown(f"**{record.name}**")
            c2.caption(record.extension.upper().lstrip("."))
            c3.caption(record.size_label)
            c4.caption(f"{record.chunk_count} chunks")

with summary_tab:
    st.subheader("Executive summaries")
    selected_document = st.selectbox("Document", workspace.document_names, key="summary_document")
    if st.button("Generate summary", type="primary"):
        try:
            with st.spinner("Creating an evidence-grounded executive summary…"):
                summary = workspace.summarize(selected_document)
            st.session_state.summary_cache[selected_document] = summary
        except Exception as exc:
            st.error(f"Could not summarize the document: {exc}")

    cached_summary = st.session_state.summary_cache.get(selected_document)
    if cached_summary:
        st.markdown(cached_summary)
        st.download_button(
            "Download summary",
            data=f"# Summary: {selected_document}\n\n{cached_summary}\n",
            file_name=f"{Path(selected_document).stem}_summary.md",
            mime="text/markdown",
        )

with search_tab:
    st.subheader("Semantic search")
    st.caption("Search by meaning rather than exact keywords.")
    search_query = st.text_input("Search query", placeholder="e.g. remote work approval policy")
    if st.button("Search documents") and search_query.strip():
        try:
            with st.spinner("Finding the most relevant passages…"):
                search_results = workspace.search(search_query, top_k=8)
            if not search_results:
                st.info("No results found.")
            for rank, result in enumerate(search_results, start=1):
                with st.container(border=True):
                    st.markdown(f"**{rank}. {result.chunk.citation_label}**")
                    st.caption(f"Similarity score: {result.score:.3f}")
                    st.write(result.chunk.text)
        except Exception as exc:
            st.error(f"Search failed: {exc}")

with compare_tab:
    st.subheader("Compare two documents")
    if len(workspace.document_names) < 2:
        st.info("Upload at least two documents to use comparison mode.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            first = st.selectbox("Document A", workspace.document_names, index=0)
        with c2:
            second = st.selectbox("Document B", workspace.document_names, index=1)
        cache_key = (first, second)
        if st.button("Compare documents", type="primary"):
            try:
                with st.spinner("Comparing the documents…"):
                    comparison = workspace.compare(first, second)
                st.session_state.comparison_cache[cache_key] = comparison
            except Exception as exc:
                st.error(f"Comparison failed: {exc}")

        comparison = st.session_state.comparison_cache.get(cache_key)
        if comparison:
            st.markdown(comparison)
