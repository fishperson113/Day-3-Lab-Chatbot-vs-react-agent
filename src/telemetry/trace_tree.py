import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

class TraceTree:
    """
    LangSmith-style trace tree for ReAct agent debugging.
    Each trace is a tree of nodes: LLM Call → Thought → Action → Tool → Observation → Final Answer
    """
    def __init__(self, root_input: str, mode: str, model: str):
        self.root = {
            "type": "root",
            "name": f"{mode.upper()} Run",
            "input": root_input,
            "model": model,
            "mode": mode,
            "status": "pending",
            "children": [],
            "start_time": datetime.utcnow().isoformat(),
            "latency_ms": 0,
            "total_tokens": 0,
            "cost_estimate": 0.0
        }
        self.current_step = None

    def add_step(self, llm_output: str, latency_ms: int, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Add an LLM call step to the tree."""
        step_node = {
            "type": "llm_call",
            "name": f"LLM Call #{len(self.root['children']) + 1}",
            "output": llm_output,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "children": [],
            "start_time": datetime.utcnow().isoformat()
        }
        self.root["children"].append(step_node)
        self.current_step = step_node
        return step_node

    def add_action(self, tool_name: str, args: str):
        """Add an Action node under the current step."""
        if self.current_step is None:
            return
        action_node = {
            "type": "action",
            "name": f"Action: {tool_name}",
            "tool": tool_name,
            "args": args,
            "status": "pending",
            "start_time": datetime.utcnow().isoformat()
        }
        self.current_step["children"].append(action_node)
        return action_node

    def add_observation(self, observation: str):
        """Add an Observation node after tool execution."""
        if self.current_step is None:
            return
        obs_node = {
            "type": "observation",
            "name": f"Observation",
            "result": observation,
            "start_time": datetime.utcnow().isoformat()
        }
        self.current_step["children"].append(obs_node)
        return obs_node

    def add_final_answer(self, answer: str):
        """Mark the final answer in the tree."""
        final_node = {
            "type": "final_answer",
            "name": "Final Answer",
            "content": answer,
            "start_time": datetime.utcnow().isoformat()
        }
        self.root["children"].append(final_node)
        self.root["status"] = "success"
        return final_node

    def mark_error(self, error: str):
        """Mark the trace as errored."""
        self.root["status"] = "error"
        self.root["error"] = error

    def finalize(self, total_latency_ms: int, total_tokens: int = 0, cost: float = 0.0):
        """Finalize the trace with summary stats."""
        self.root["latency_ms"] = total_latency_ms
        self.root["total_tokens"] = total_tokens
        self.root["cost_estimate"] = cost
        self.root["end_time"] = datetime.utcnow().isoformat()
        if self.root["status"] == "pending":
            self.root["status"] = "success"

    def to_dict(self) -> Dict:
        return self.root

    @staticmethod
    def from_dict(data: Dict) -> 'TraceTree':
        """Reconstruct (for display purposes, just return dict)."""
        return data  # For simplicity, just pass dict through


class TraceLogger:
    """
    LangSmith-style trace logger.
    Writes tree traces to JSONL with full nesting.
    """
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.active_traces: Dict[str, TraceTree] = {}

    def start_trace(self, trace_id: str, root_input: str, mode: str, model: str) -> TraceTree:
        """Start a new trace tree."""
        tree = TraceTree(root_input, mode, model)
        self.active_traces[trace_id] = tree
        return tree

    def end_trace(self, trace_id: str):
        """End a trace and persist to file."""
        tree = self.active_traces.pop(trace_id, None)
        if tree:
            self._persist(tree.to_dict())

    def _persist(self, trace_data: Dict):
        """Write trace to JSONL file."""
        trace_file = os.path.join(self.log_dir, f"traces_tree_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_data, ensure_ascii=False) + "\n")

    def load_traces(self, limit: int = 50) -> List[Dict]:
        """Load recent traces from file."""
        trace_file = os.path.join(self.log_dir, f"traces_tree_{datetime.now().strftime('%Y%m%d')}.jsonl")
        traces = []
        if os.path.exists(trace_file):
            with open(trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        traces.append(json.loads(line))
        return traces[-limit:]  # Return latest N

# Global instance
trace_logger = TraceLogger()
