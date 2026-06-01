import os
import sys
import streamlit as st
from main import create_worker, TOOLS
from src.agent.agent import ReActAgent
from src.chatbot import SimpleChatbot
from src.telemetry.metrics import recorder
from src.telemetry.trace_tree import trace_logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__name__)))

def initialize_session(mode: str, provider: str):
    with st.spinner(f"Loading {mode.upper()} mode with {provider.upper()}..."):
        worker = create_worker(mode, provider)
        st.session_state.worker = worker
        st.session_state.mode = mode
        st.session_state.provider = provider
        st.session_state.history = []
        st.session_state.session_ready = True
        if isinstance(worker, ReActAgent):
            worker.clear_memory()

def render_node(node):
    icon = "🤖" if node["type"] == "llm_call" else "🛠️" if node["type"] == "action" else "👁️" if node["type"] == "observation" else "✅"
    label = f"{icon} {node['name']}"
    if "latency_ms" in node and node["latency_ms"] > 0:
        label += f" ({node['latency_ms']}ms)"

    with st.expander(label, expanded=(node["type"] in ["action", "final_answer"])):
        if node["type"] == "llm_call":
            st.code(node["output"])
            if "prompt_tokens" in node:
                st.caption(f"Tokens: {node['prompt_tokens']} prompt + {node['completion_tokens']} completion")
        elif node["type"] == "action":
            st.info(f"Arguments: `{node['args']}`")
        elif node["type"] == "observation":
            st.success(node["result"])
        elif node["type"] == "final_answer":
            st.write(node["content"])

        if "children" in node:
            for child in node["children"]:
                render_node(child)

def render_chat():
    st.write("Using Gemma 3 1B (Local) or GPT-5 (NineRouter).")
    for chat in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("assistant"):
            st.markdown(chat["ai"])
            st.caption(f"Latency: {chat['latency']}ms | Steps: {chat['steps']}")

    if prompt := st.chat_input("Ask a question..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.worker.run(prompt)
                    response = result.get("response", str(result))
                    latency = result.get("latency_ms", 0)
                    steps = result.get("steps", 0)
                    st.markdown(response)
                    st.caption(f"Latency: {latency}ms | Steps: {steps}")
                    st.session_state.history.append({
                        "user": prompt, "ai": response, "latency": latency, "steps": steps
                    })
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def render_comparison():
    st.header("🆚 Chatbot vs Agent Comparison")
    st.write("Compare results for the exact same input.")

    traces = recorder.load_all()
    if not traces:
        st.info("Run some tests in both modes first!")
        return

    all_inputs = list(set([t["input"] for t in traces]))
    selected_input = st.selectbox("Select a query to compare", all_inputs)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Chatbot")
        c_trace = next((t for t in reversed(traces) if t["input"] == selected_input and t["mode"] == "chatbot"), None)
        if c_trace:
            st.info(c_trace["response"])
            st.caption(f"Latency: {c_trace['latency_ms']}ms | Cost: ${c_trace['cost_estimate']:.5f}")
        else: st.warning("No chatbot trace.")

    with col2:
        st.subheader("🧠 ReAct Agent")
        a_trace = next((t for t in reversed(traces) if t["input"] == selected_input and t["mode"] == "agent"), None)
        if a_trace:
            st.success(a_trace["response"])
            st.caption(f"Latency: {a_trace['latency_ms']}ms | Steps: {a_trace['steps']} | Cost: ${a_trace['cost_estimate']:.5f}")
            if a_trace.get("history"):
                with st.expander("Reasoning Path"):
                    for h in a_trace["history"]:
                        st.write(f"🛠️ {h['action']} → 👁️ {h['observation']}")
        else: st.warning("No agent trace.")

def render_dashboard():
    st.header("📊 Performance & Traces")
    tabs = st.tabs(["Overview", "Side-by-Side Comparison", "Trace Tree (LangSmith)", "Raw Data"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Chatbot Baseline")
            s = recorder.get_summary(mode="chatbot")
            if s.get("total_cases", 0) > 0:
                st.metric("Success Rate", f"{s['success_rate']}%")
                st.metric("Avg Latency", f"{s['p50_latency_ms']}ms")
                st.metric("Total Cost", f"${s['total_cost']:.4f}")
            else: st.info("No data.")
        with col2:
            st.subheader("ReAct Agent")
            s = recorder.get_summary(mode="agent")
            if s.get("total_cases", 0) > 0:
                st.metric("Success Rate", f"{s['success_rate']}%")
                st.metric("Avg Steps", s['avg_steps'])
                st.metric("Total Cost", f"${s['total_cost']:.4f}")
            else: st.info("No data.")

    with tabs[1]:
        render_comparison()

    with tabs[2]:
        st.subheader("Trace Tree Analysis")
        traces = trace_logger.load_traces(limit=10)
        if not traces: st.info("No traces yet.")
        else:
            selected_trace = st.selectbox("Select a trace to inspect",
                                         options=range(len(traces)),
                                         format_func=lambda i: f"{traces[i].get('start_time', 'N/A')} - {traces[i].get('input', 'N/A')[:40]}...",
                                         index=len(traces)-1)
            trace = traces[selected_trace]
            st.write(f"**Model:** {trace['model']} | **Status:** {trace['status']} | **Total Latency:** {trace['latency_ms']}ms")
            for child in trace["children"]:
                render_node(child)

    with tabs[3]:
        st.subheader("Raw Metrics")
        m = recorder.load_all()
        if m:
            import pandas as pd
            st.dataframe(pd.DataFrame(m[::-1]))

def main():
    st.set_page_config(page_title="Agent Tracer UI", layout="wide")
    if "session_ready" not in st.session_state: st.session_state.session_ready = False
    if "history" not in st.session_state: st.session_state.history = []

    st.title("🛍️ Retail AI Assistant")
    with st.sidebar:
        st.header("Settings")
        provider = st.selectbox("LLM Provider", ["hf", "openai"], format_func=lambda x: "Local Gemma 3" if x == "hf" else "NineRouter GPT-5")
        mode = st.radio("Mode", ["chatbot", "agent"], index=1)
        if st.button("Start/Reset Session"): initialize_session(mode.lower(), provider.lower())
        if st.session_state.get("session_ready"):
            st.success(f"Active: {st.session_state.mode.upper()} ({st.session_state.provider.upper()})")

    main_tabs = st.tabs(["💬 Chat", "📊 Metrics & Traces"])
    with main_tabs[0]:
        if not st.session_state.session_ready: st.info("👈 Please initialize session to start.")
        else: render_chat()
    with main_tabs[1]: render_dashboard()

if __name__ == "__main__":
    main()
