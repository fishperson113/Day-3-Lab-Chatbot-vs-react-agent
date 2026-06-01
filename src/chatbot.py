import time
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import recorder

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
        start_time = time.time()
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        system_prompt = """Bạn là nhân viên bán hàng.
Luật:
1. Trả lời cực kỳ NGẮN GỌN (dưới 3 câu).
2. Nếu không có thông tin đơn hàng, hãy từ chối ngay. Không suy đoán, không dông dài.

Mẫu 1:
User: Đơn ORD123 nặng bao nhiêu?
Assistant: Tôi không có quyền truy cập hệ thống để xem đơn hàng này.

Mẫu 2:
User: 1 + 1 bằng mấy?
Assistant: 1 + 1 bằng 2."""

        result = self.llm.generate(user_input, system_prompt=system_prompt)
        response_text = result.get("content", str(result))
        latency_ms = int((time.time() - start_time) * 1000)

        usage = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        cost = recorder.calculate_cost(self.llm.model_name, usage["prompt_tokens"], usage["completion_tokens"])

        # Record trace for evaluation
        trace = {
            "mode": "chatbot",
            "model": self.llm.model_name,
            "input": user_input,
            "response": response_text,
            "latency_ms": latency_ms,
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "total_tokens": usage["total_tokens"],
            "cost_estimate": cost,
            "steps": 1,
            "status": "success"
        }
        recorder.record(trace)
        logger.log_event("CHATBOT_END", {"model": self.llm.model_name})

        return trace

if __name__ == "__main__":
    load_dotenv()
    # Simple test
    from src.core.hf_provider import HFProvider
    llm = HFProvider()
    bot = SimpleChatbot(llm)
    print(bot.run("ORD123 nặng bao nhiêu?"))
