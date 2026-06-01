import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools.retail_tools import TOOLS_MAPPING
from src.core.hf_provider import HFProvider

AVAILABLE_PROVIDERS = ["hf", "local", "openai", "gemini"]
AVAILABLE_MODES = ["chatbot", "agent"]

TOOLS = [
    {"name": "get_order_weight", "description": "Lấy cân nặng đơn hàng", "function": TOOLS_MAPPING["get_order_weight"]},
    {"name": "calculate_shipping", "description": "Tính phí ship", "function": TOOLS_MAPPING["calculate_shipping"]},
    {"name": "check_stock", "description": "Kiểm tra tồn kho", "function": TOOLS_MAPPING["check_stock"]}
]


def build_provider(provider_name: str, local_model_path: str | None = None):
    provider = provider_name.lower()
    if provider == "hf":
        return HFProvider(model_id=os.getenv("HF_MODEL_ID", "google/gemma-3-1b-it"))

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

    if provider == "gemini":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=os.getenv("GOOGLE_API_KEY"))

    if provider == "local":
        from src.core.local_provider import LocalProvider
        model_path = local_model_path or os.getenv("LOCAL_MODEL_PATH")
        if not model_path:
            raise ValueError("Local model path is required for the local provider.")
        return LocalProvider(model_path=model_path)

    raise ValueError(f"Unknown provider '{provider_name}'")


def build_worker(mode: str, llm):
    if mode == "agent":
        return ReActAgent(llm=llm, tools=TOOLS)
    return SimpleChatbot(llm=llm)


def initialize_session(provider: str, mode: str, local_path: str | None = None):
    llm = build_provider(provider, local_path)
    worker = build_worker(mode, llm)
    st.session_state.provider = provider
    st.session_state.mode = mode
    st.session_state.worker = worker
    st.session_state.history = []
    st.session_state.session_ready = True


def clear_session():
    st.session_state.provider = None
    st.session_state.mode = None
    st.session_state.worker = None
    st.session_state.history = []
    st.session_state.session_ready = False
    st.session_state.status_message = ""
    st.session_state.error_message = ""
    st.session_state.local_model_path = ""


def ensure_state():
    if "provider" not in st.session_state:
        clear_session()
    if "status_message" not in st.session_state:
        st.session_state.status_message = ""
    if "error_message" not in st.session_state:
        st.session_state.error_message = ""
    if "local_model_path" not in st.session_state:
        st.session_state.local_model_path = ""
    if "input_message" not in st.session_state:
        st.session_state.input_message = ""


def inject_styles():
    st.markdown(
        """
        <style>
        .streamlit-expanderHeader {
            font-size: 1.05rem !important;
        }
        .css-18ni7ap.e8zbici2 {
            padding: 0 !important;
        }
        .card {
            border-radius: 24px;
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
            padding: 24px;
            margin-bottom: 24px;
        }
        .chat-bubble {
            border-radius: 20px;
            padding: 18px;
            margin-bottom: 16px;
            line-height: 1.65;
        }
        .chat-user {
            background: #eef2ff;
            border: 1px solid #c7d2fe;
        }
        .chat-ai {
            background: #fff7ed;
            border: 1px solid #fed7aa;
        }
        .chat-meta {
            color: #475569;
            font-size: 0.92rem;
            margin-top: 10px;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 8px 14px;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-weight: 700;
            margin-right: 10px;
            margin-bottom: 12px;
        }
        .headline {
            font-size: clamp(2rem, 2.2vw, 2.6rem);
            margin-bottom: 10px;
        }
        .subtext {
            color: #475569;
            margin-bottom: 18px;
        }
        .streamlit-button {
            border-radius: 14px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.header("Session setup")
        provider = st.selectbox("Provider", AVAILABLE_PROVIDERS, index=0)
        mode = st.selectbox("Mode", AVAILABLE_MODES, index=0)
        local_model_path = st.text_input(
            "Local model path (.gguf)",
            value=st.session_state.local_model_path,
            placeholder="/path/to/model.gguf",
        )

        if st.button("Initialize session"):
            try:
                initialize_session(provider, mode, local_model_path if local_model_path else None)
                st.session_state.status_message = f"Loaded {mode.upper()} with {provider.upper()} successfully."
                st.session_state.error_message = ""
            except Exception as exc:
                st.session_state.error_message = str(exc)
                st.session_state.status_message = ""

        if st.button("Reset session"):
            clear_session()

        if st.session_state.error_message:
            st.error(st.session_state.error_message)
        elif st.session_state.status_message:
            st.success(st.session_state.status_message)

        st.markdown("---")
        st.markdown(
            "Use the UI to select a provider and mode. Only one worker loads at a time, and the chat runs one request at a time."
        )

    return provider, mode, local_model_path


def render_main():
    st.title("Agent Streamlit Interface")
    st.write(
        "A small interactive wrapper for your chatbot and ReAct agent. Select a provider, initialize a session, then send one prompt at a time."
    )

    if not st.session_state.session_ready or st.session_state.worker is None:
        st.info("Configure the session from the sidebar and click Initialize to start.")
        return

    st.markdown(
        f"<div class=\"status-pill\">Provider: {st.session_state.provider.upper()}</div>"
        f"<div class=\"status-pill\">Mode: {st.session_state.mode.title()}</div>",
        unsafe_allow_html=True,
    )

    with st.form(key="chat_form"):
        prompt = st.text_area("Your message", key="input_message", height=180)
        submitted = st.form_submit_button("Send")

    if submitted:
        if not prompt.strip():
            st.warning("Please enter a message before sending.")
        else:
            try:
                raw_response = st.session_state.worker.run(prompt)
                response_text = raw_response.get("response") if isinstance(raw_response, dict) else str(raw_response)
                latency = raw_response.get("latency_ms") if isinstance(raw_response, dict) else None
                st.session_state.history.append(
                    {
                        "user": prompt,
                        "ai": response_text,
                        "latency": latency,
                    }
                )
                st.session_state.input_message = ""
            except Exception as exc:
                st.error(f"Error running the session: {exc}")

    if st.session_state.history:
        st.markdown("## Conversation")
        for i, item in enumerate(st.session_state.history, start=1):
            st.markdown(
                f"<div class=\"chat-bubble chat-user\"><strong>You</strong><div>{item['user']}</div></div>"
                f"<div class=\"chat-bubble chat-ai\"><strong>AI</strong><div>{item['ai']}</div>"
                f"<div class=\"chat-meta\">Latency: {item['latency'] if item['latency'] is not None else 'n/a'} ms</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<div class='card'><p class='subtext'>No conversation yet. Send your first prompt to start.</p></div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Agent Streamlit UI", layout="wide")
    ensure_state()
    inject_styles()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
