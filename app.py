import os
import time

import requests
import streamlit as st

DEFAULT_API_URL = os.environ.get(
    "API_URL", "https://develop-suspension-spend-pontiac.trycloudflare.com"
)

EXAMPLE_QUESTIONS = [
    "What is COMFIE?",
    "Which tools are used for data curation?",
    "What methodologies are available for digital projects?",
]

st.set_page_config(page_title="Testware Catalogue RAG", page_icon="🔎", layout="centered")

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input(
        "RAG API URL",
        value=DEFAULT_API_URL,
        help="Your cloudflared tunnel URL — changes every time you restart the tunnel.",
    ).rstrip("/")
    st.divider()
    st.header("Try an example")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

st.title("🔎 Testware Catalogue RAG")
st.caption("Ask a question about the testware catalogue — answers are grounded in retrieved sources.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


def stream_words(text: str, delay: float = 0.02):
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)


def ask(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the catalogue..."):
            try:
                resp = requests.post(f"{api_url}/query", json={"query": question}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])
            except requests.RequestException as exc:
                answer = f"Couldn't reach the RAG API — is the tunnel still running? ({exc})"
                sources = []

        st.write_stream(stream_words(answer))

        if sources:
            with st.expander(f"📚 {len(sources)} source(s)"):
                for s in sources:
                    st.markdown(f"**{s.get('source_file', 'unknown')}**")
                    st.caption(s.get("excerpt", ""))
                    st.divider()

    st.session_state.messages.append({"role": "assistant", "content": answer})


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.pending_question:
    pending = st.session_state.pending_question
    st.session_state.pending_question = None
    ask(pending)

if question := st.chat_input("Ask about the testware catalogue..."):
    ask(question)
