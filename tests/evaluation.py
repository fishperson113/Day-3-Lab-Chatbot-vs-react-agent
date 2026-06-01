import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO (Person C): Define your test cases here
# Format: {"input": "Your question", "expected_steps": "simple/multi-step"}

TEST_CASES = [
    {
        "input": "Chào bạn, bạn có thể giúp gì cho tôi?",
        "type": "simple"
    },
    {
        "input": "Đơn hàng ORD123 của tôi nặng bao nhiêu kg?",
        "type": "multi-step"
    },
    {
        "input": "Tôi ở Hanoi, đơn hàng ORD123 nặng 1.0kg thì phí ship bao nhiêu?",
        "type": "multi-step"
    },
    {
        "input": "Tính tổng phí: xem đơn ORD123 nặng bao nhiêu rồi tính phí ship về Hanoi hộ tôi.",
        "type": "reasoning"
    }
]

def run_evaluation():
    """
    TODO (Person C & D):
    1. Loop through TEST_CASES.
    2. Run both Chatbot and Agent.
    3. Compare results and log metrics.
    """
    print("Evaluation script starting...")

if __name__ == "__main__":
    run_evaluation()
