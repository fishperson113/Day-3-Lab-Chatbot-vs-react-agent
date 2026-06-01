# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Le Sy Han
- **Student ID**: 2A202600790
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

I implemented three key files for this lab: `src/chatbot.py`, `tests/evaluation.py`, and `interface.py`.

- **Modules Implemented**:
  - `src/chatbot.py`: Added a `SimpleChatbot` wrapper that calls the LLM provider with a single prompt, measures latency, and returns structured response objects. It also supports standalone CLI execution based on the configured provider.
  - `tests/evaluation.py`: Built an evaluation harness comparing the direct chatbot against the ReAct agent over a set of scripted test cases. It collects both response text and latency, then exports results to a JSON file.
  - `interface.py`: Created a separate Streamlit-based frontend interface so the user can choose provider/mode and interact with the system in a user-friendly way without modifying `main.py`.

- **Code Highlights**:
  - `src/chatbot.py` centralizes a non-ReAct baseline path with `SimpleChatbot.run()` returning `{question, response, latency_ms}`.
  - `tests/evaluation.py` includes `get_provider()` to select OpenAI/Gemini/local from environment variables and `run_evaluation()` to produce a full comparison report.
  - `interface.py` uses Streamlit session state to initialize exactly one model/session at a time, supports provider selection, and adds a styled chat UI.

- **Documentation**:
  - The `SimpleChatbot` implementation emphasizes direct answer generation without tool reasoning.
  - The `ReActAgent` remains the reasoning path, while `tests/evaluation.py` lets both paths run side by side on identical prompts.
  - The Streamlit interface intentionally avoids parallel startup of multiple LLMs; it loads one selected worker per session.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: When implementing the Streamlit interface, the local provider sometimes failed during session initialization because the local model path was not provided.

- **Log Source**: Although this lab did not produce a dedicated external log file for this issue, the error surfaced directly during the interface startup flow in the browser and from Python exceptions in `interface.py`.

- **Diagnosis**: The crash was caused by missing validation for `LOCAL_MODEL_PATH` before constructing `LocalProvider`. The session code attempted to build the provider immediately after form submission, so `None` or an empty string triggered a `ValueError`.

- **Solution**: I added explicit local model path validation in `interface.py` and provided a clear user-facing message when the local provider was selected without a valid `.gguf` path. This prevents the interface from loading an invalid session.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: The `Thought` block in the agent prompt helps the ReAct agent break down multi-step tasks into tool calls and observations. For questions that require sequential reasoning, the agent can explicitly choose actions, inspect results, and then produce a final response.

2. **Reliability**: The agent may perform worse than the chatbot on simple conversational questions because the ReAct loop adds overhead and can overcomplicate an answer. In direct prompts like greetings or simple arithmetic, the baseline chatbot is often faster and more stable.

3. **Observation**: Observations act as environment feedback that guides the next step. Each tool call result is appended back into the prompt, so the agent can refine its next thought or choose a different tool, while the chatbot has no such feedback loop.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Separate the frontend, agent orchestration, and tool execution into microservices or an asynchronous task queue. This would allow more tools and providers to be added without blocking the UI.
- **Safety**: Add a validation layer to verify tool actions before execution, and consider a supervisory LLM that audits the agent's proposed `Action` calls.
- **Performance**: Cache tool results and use a lightweight local model for fast baseline responses. For reasoning tasks, a larger model can be used selectively.

---

> [!NOTE]
> This report is based on the implementation of `src/chatbot.py`, `tests/evaluation.py`, and `interface.py` for Lab 3.
