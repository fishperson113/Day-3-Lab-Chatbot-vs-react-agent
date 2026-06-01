import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider


TEST_CASES = [
    {
        "input": "Chào bạn, bạn có thể giúp gì cho tôi?",
        "type": "simple"
    },
    {
        "input": "1 + 1 bằng mấy?",
        "type": "simple"
    },
    {
        "input": "Đơn hàng ORD123 của tôi nặng bao nhiêu kg?",
        "type": "multi-step"
    },
    {
        "input": "Kiểm tra tồn kho iPhone.",
        "type": "multi-step"
    },
    {
        "input": "Tôi ở Hanoi, đơn hàng ORD123 nặng 1.0kg thì phí ship bao nhiêu?",
        "type": "multi-step"
    },
    {
        "input": "Tính tổng phí: xem đơn ORD123 nặng bao nhiêu rồi tính phí ship về Hanoi hộ tôi.",
        "type": "reasoning"
    },
    {
        "input": "Tôi muốn mua 2 iPhone, có đủ hàng không?",
        "type": "reasoning"
    },
    {
        "input": "Tôi muốn mua 20 iPhone, có đủ hàng không?",
        "type": "reasoning"
    }
]


def get_provider():
    provider = os.getenv("DEFAULT_PROVIDER", "local").lower()

    if provider == "openai":
        return OpenAIProvider()

    if provider == "gemini":
        return GeminiProvider()

    return LocalProvider()


def run_evaluation():

    load_dotenv()

    llm = get_provider()

    chatbot = SimpleChatbot(llm)
    agent = ReActAgent(llm)

    results = []

    chatbot_total_latency = 0
    agent_total_latency = 0

    print("\nSTARTING EVALUATION\n")

    for idx, case in enumerate(TEST_CASES, start=1):

        question = case["input"]

        print("\n" + "=" * 80)
        print(f"TEST {idx}")
        print(f"TYPE: {case['type']}")
        print(f"QUESTION: {question}")

        print("\n[CHATBOT]")
        chatbot_result = chatbot.run(question)

        print("\n[AGENT]")
        agent_result = agent.run(question)

        chatbot_total_latency += chatbot_result.get("latency_ms", 0)
        agent_total_latency += agent_result.get("latency_ms", 0)

        results.append(
            {
                "test_id": idx,
                "type": case["type"],
                "question": question,

                "chatbot_response":
                    chatbot_result.get("response", ""),

                "chatbot_latency_ms":
                    chatbot_result.get("latency_ms", 0),

                "agent_response":
                    agent_result.get("response", ""),

                "agent_latency_ms":
                    agent_result.get("latency_ms", 0),
            }
        )

    total_cases = len(TEST_CASES)

    summary = {
        "total_cases": total_cases,
        "chatbot_avg_latency_ms":
            chatbot_total_latency / total_cases,

        "agent_avg_latency_ms":
            agent_total_latency / total_cases
    }

    output = {
        "summary": summary,
        "results": results
    }

    filename = (
        f"evaluation_results_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n" + "=" * 80)
    print("EVALUATION FINISHED")
    print("=" * 80)

    print(
        f"Chatbot Avg Latency: "
        f"{summary['chatbot_avg_latency_ms']:.2f} ms"
    )

    print(
        f"Agent Avg Latency: "
        f"{summary['agent_avg_latency_ms']:.2f} ms"
    )

    print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    run_evaluation()