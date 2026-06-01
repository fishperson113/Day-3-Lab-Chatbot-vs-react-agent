import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

class IndustryLogger:
    """Structured logger that logs traces to JSONL files."""
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.log_dir = log_dir

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # JSONL trace file for the current session
        self.trace_file = os.path.join(log_dir, f"traces_{datetime.now().strftime('%Y%m%d')}.jsonl")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs an event to JSONL file."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        # Write to JSONL file
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        # Also print to console
        print(json.dumps(payload, ensure_ascii=False))

    def log_trace(self, trace: Dict[str, Any]):
        """Logs a complete trace (single conversation turn)."""
        trace["timestamp"] = datetime.utcnow().isoformat()
        trace["event"] = "TRACE"
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

    def get_all_traces(self) -> list:
        """Read all traces from today's log file."""
        traces = []
        if os.path.exists(self.trace_file):
            with open(self.trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        traces.append(json.loads(line))
        return traces

    def get_traces_by_type(self, event_type: str) -> list:
        """Filter traces by event type."""
        return [t for t in self.get_all_traces() if t.get("event") == event_type]

# Global logger instance
logger = IndustryLogger()
