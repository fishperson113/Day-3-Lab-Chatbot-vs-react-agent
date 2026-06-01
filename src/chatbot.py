import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.telemetry.logger import logger

class SimpleChatbot:
    """
    TODO (Person C): Implement a clean, minimal chatbot baseline.
    This chatbot should just call the LLM directly without any ReAct loop.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> str:
        """
        TODO (Person C):
        1. Log event "CHATBOT_START"
        2. Call self.llm.generate()
        3. Log event "CHATBOT_END"
        4. Return content
        """
        return "Chatbot not implemented. Fill in the TODOs!"

if __name__ == "__main__":
    # TODO (Person C): Setup provider and run test cases
    print("Chatbot entry point.")
