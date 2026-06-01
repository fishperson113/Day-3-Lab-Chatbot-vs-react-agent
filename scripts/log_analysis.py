import json
import os
import statistics
from typing import Any, Dict, List

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def parse_json_log_file(path: str) -> List[Dict[str, Any]]:
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: failed to parse line: {line}")
    return events


def analyze_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = []
    failure_traces = []
    loop_counts = []

    for event in events:
        if event.get("event") == "LLM_METRIC":
            data = event.get("data", {})
            metrics.append(data)
        if event.get("event") == "AGENT_END":
            data = event.get("data", {})
            if "loop_count" in data:
                loop_counts.append(data["loop_count"])
        if event.get("event") in ["AGENT_PARSE_ERROR", "TOOL_ERROR", "AGENT_END"]:
            data = event.get("data", {})
            status = data.get("status", "")
            if status in ["max_steps_reached", "parse_error"]:
                failure_traces.append(event)
        if event.get("event") == "AGENT_PARSE_ERROR":
            failure_traces.append(event)

    latencies = [m["latency_ms"] for m in metrics if "latency_ms" in m]
    prompt_tokens = [m["prompt_tokens"] for m in metrics if "prompt_tokens" in m]
    completion_tokens = [m["completion_tokens"] for m in metrics if "completion_tokens" in m]
    cost_estimates = [m["cost_estimate"] for m in metrics if "cost_estimate" in m]

    analysis = {
        "metrics_count": len(metrics),
        "loop_counts": loop_counts,
        "latency_ms": latencies,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_estimate": cost_estimates,
        "p50_latency_ms": statistics.median(latencies) if latencies else None,
        "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 2 else (latencies[-1] if latencies else None),
        "failure_traces": failure_traces,
    }
    return analysis


def main() -> None:
    log_files = sorted(
        [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    )

    if not log_files:
        print("No log files found.")
        return

    for log_file in log_files:
        path = os.path.join(LOG_DIR, log_file)
        events = parse_json_log_file(path)
        analysis = analyze_events(events)

        print("=" * 80)
        print(f"Log file: {log_file}")
        print(f"Total metrics events: {analysis['metrics_count']}")
        print(f"Loop counts: {analysis['loop_counts']}")
        print(f"P50 latency (ms): {analysis['p50_latency_ms']}")
        print(f"P99 latency (ms): {analysis['p99_latency_ms']}")
        print(f"Prompt tokens: {analysis['prompt_tokens']}")
        print(f"Completion tokens: {analysis['completion_tokens']}")
        print(f"Cost estimates: {analysis['cost_estimate']}")
        print(f"Failure traces: {len(analysis['failure_traces'])}")
        if analysis['failure_traces']:
            print(json.dumps(analysis['failure_traces'], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
