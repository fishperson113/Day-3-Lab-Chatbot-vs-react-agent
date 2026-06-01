import time
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider


class SimpleChatbot:
    """
    Baseline chatbot:
    - No ReAct loop
    - No tool usage
    - Single LLM call
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> dict:
        start = time.time()

        print("=" * 50)
        print("[CHATBOT] START")
        print(f"User: {user_input}")

        response = self.llm.generate(user_input)

        print(f"Assistant: {response}")
        print("[CHATBOT] END")
        print("=" * 50)

        latency_ms = int((time.time() - start) * 1000)

        return {
            "question": user_input,
            "response": response,
            "latency_ms": latency_ms,
        }


if __name__ == "__main__":
    load_dotenv()

    from src.core.openai_provider import OpenAIProvider
    from src.core.gemini_provider import GeminiProvider
    from src.core.local_provider import LocalProvider

    provider = os.getenv("DEFAULT_PROVIDER", "local").lower()

    if provider == "openai":
        llm = OpenAIProvider()
    elif provider == "gemini":
        llm = GeminiProvider()
    else:
        llm = LocalProvider()

    chatbot = SimpleChatbot(llm)

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        result = chatbot.run(user_input)

        print(f"\nBot: {result['response']}")
        print(f"Latency: {result['latency_ms']} ms")