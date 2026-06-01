"""
Backend module for Lab 3: CLI + Streamlit entry point.
Usage:
    uv run main.py [chatbot|agent]    # CLI mode
    uv run streamlit run interface.py  # UI mode
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.hf_provider import HFProvider
from src.core.openai_provider import OpenAIProvider
from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools.retail_tools import TOOLS_MAPPING

TOOLS = [
    {"name": "get_order_weight", "description": "Get order weight by order ID. Input: order_id (e.g. ORD123). Output: '1.0 kg'."},
    {"name": "calculate_shipping", "description": "Calculate shipping fee. Input: weight|province (e.g. 1.0|Hanoi). Output: '5000 VND'."},
    {"name": "check_stock", "description": "Check product stock. Input: product name (e.g. iphone). Output: '10 units in stock'."}
]

def create_worker(mode: str, provider: str = "hf"):
    """Create worker (chatbot or agent) with provider + tools."""
    if provider == "openai":
        llm = OpenAIProvider(
            model_name=os.getenv("NINEROUTER_MODEL", "openai/gpt-5"),
            api_key=os.getenv("NINEROUTER_KEY"),
            base_url=os.getenv("NINEROUTER_URL")
        )
    else:
        llm = HFProvider(model_id=os.getenv("HF_MODEL_ID", "google/gemma-3-1b-it"))

    if mode == "agent":
        return ReActAgent(llm=llm, tools=TOOLS)
    return SimpleChatbot(llm=llm)

def run_cli():
    """CLI entry point."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "chatbot"
    provider = os.getenv("DEFAULT_PROVIDER", "hf")
    worker = create_worker(mode, provider)

    print(f"\n=== Running in {mode.upper()} mode using {provider.upper()} ===\n")
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            result = worker.run(user_input)
            if isinstance(result, dict):
                print(f"AI: {result.get('response', '')}")
                print(f"[Latency: {result.get('latency_ms', 0)}ms]", end="")
                if result.get("steps"):
                    print(f" | Steps: {result['steps']}", end="")
                print()
            else:
                print(f"AI: {result}")
            print()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    run_cli()
