import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Model pricing (per 1K tokens, USD)
MODEL_PRICING = {
    "google/gemma-3-1b-it": {"input": 0.0, "output": 0.0},  # Local model = free
    "openai/gpt-5": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.01, "output": 0.03},
    "gemini-1.5-flash": {"input": 0.0005, "output": 0.0015},
}

class TraceRecorder:
    """
    Records and analyzes conversation traces for SCORING.md.
    Metrics: latency, tokens, cost, steps, success/failure.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.traces: List[Dict] = []

    def record(self, trace: Dict[str, Any]):
        """Record a single trace (one conversation turn)."""
        trace["recorded_at"] = datetime.utcnow().isoformat()
        self.traces.append(trace)

        # Append to JSONL file
        trace_file = os.path.join(self.log_dir, "metrics.jsonl")
        with open(trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

    def load_all(self) -> List[Dict]:
        """Load all recorded traces."""
        trace_file = os.path.join(self.log_dir, "metrics.jsonl")
        if not os.path.exists(trace_file):
            return []
        with open(trace_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def get_summary(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """Compute summary metrics, optionally filtered by mode (chatbot/agent)."""
        traces = self.load_all()
        if mode:
            traces = [t for t in traces if t.get("mode") == mode]

        if not traces:
            return {"total_cases": 0}

        latencies = [t.get("latency_ms", 0) for t in traces]
        tokens = [t.get("total_tokens", 0) for t in traces]
        costs = [t.get("cost_estimate", 0) for t in traces]
        steps_list = [t.get("steps", 1) for t in traces]
        successes = [t for t in traces if t.get("status") == "success"]

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        return {
            "total_cases": len(traces),
            "success_cases": len(successes),
            "fail_cases": len(traces) - len(successes),
            "success_rate": round(len(successes) / len(traces) * 100, 1) if traces else 0,
            "avg_latency_ms": round(sum(latencies) / n, 1) if n else 0,
            "p50_latency_ms": latencies_sorted[n // 2] if n else 0,
            "p99_latency_ms": latencies_sorted[int(n * 0.99) - 1] if n >= 100 else (latencies_sorted[-1] if n else 0),
            "avg_tokens": round(sum(tokens) / n, 1) if n else 0,
            "avg_steps": round(sum(steps_list) / n, 1) if n else 0,
            "total_cost": round(sum(costs), 6),
            "avg_cost": round(sum(costs) / n, 6) if n else 0,
        }

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on model pricing."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("openai/gpt-5"))
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

# Global recorder instance
recorder = TraceRecorder()
