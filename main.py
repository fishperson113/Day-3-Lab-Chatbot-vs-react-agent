"""
Simple CLI for Lab 3 (Zero Setup via Hugging Face)
Usage: python main.py [chatbot|agent]
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.hf_provider import HFProvider
from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools.retail_tools import TOOLS_MAPPING

def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "chatbot"

    # [Inject Interface]
    # Automatically downloads model from HF if not cached
    llm = HFProvider(model_id=os.getenv("HF_MODEL_ID", "google/gemma-3-1b-it"))

    if mode == "agent":
        tools = [
            {"name": "get_order_weight", "description": "Lấy cân nặng đơn hàng", "function": TOOLS_MAPPING["get_order_weight"]},
            {"name": "calculate_shipping", "description": "Tính phí ship", "function": TOOLS_MAPPING["calculate_shipping"]},
            {"name": "check_stock", "description": "Kiểm tra tồn kho", "function": TOOLS_MAPPING["check_stock"]}
        ]
        worker = ReActAgent(llm=llm, tools=tools)
    else:
        worker = SimpleChatbot(llm=llm)

    print(f"--- Running {mode} mode (Model: {os.getenv('HF_MODEL_ID', 'google/gemma-3-1b-it')}) ---")
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]: break

            # [Call Interface]
            response = worker.run(user_input)
            print(f"AI: {response}\n")
        except KeyboardInterrupt: break

if __name__ == "__main__":
    run()
