import re
import time
import uuid
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import recorder
from src.telemetry.trace_tree import trace_logger
from src.tools.retail_tools import TOOLS_MAPPING

class ReActAgent:
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.memory = []
        self.max_memory_turns = 3

    def get_system_prompt(self) -> str:
        tool_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""Tools: {tool_desc}

You ONLY respond in these formats:
1. If tool needed: Action: tool_name|argument
2. If answering: Final Answer: your response

STRICT RULES:
- Never add extra text after Action
- Use the Observation provided by system
- Always end with Final Answer once you have info

Example:
User: How heavy is order ORD123?
Action: get_order_weight|ORD123
Observation: 1.0 kg
Final Answer: Order ORD123 weighs 1.0 kg.

Begin!"""

    def _build_prompt(self, user_input: str) -> str:
        prompt = ""
        if self.memory:
            prompt += "Recent history:\n"
            for turn in self.memory[-self.max_memory_turns:]:
                prompt += f"User: {turn['user']}\n{turn['agent']}\n\n"
        prompt += f"User: {user_input}\n"
        return prompt

    def run(self, user_input: str) -> dict:
        start_time = time.time()
        trace_id = str(uuid.uuid4())
        tree = trace_logger.start_trace(trace_id, user_input, "agent", self.llm.model_name)

        current_prompt = self._build_prompt(user_input)
        steps = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        final_response = "Sorry, I cannot answer that."

        try:
            while steps < self.max_steps:
                # LLM Call
                raw_result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
                llm_output = raw_result["content"].strip()

                usage = raw_result.get("usage", {})
                p_tokens = usage.get("prompt_tokens", 0)
                c_tokens = usage.get("completion_tokens", 0)
                total_prompt_tokens += p_tokens
                total_completion_tokens += c_tokens

                # Trace step
                tree.add_step(llm_output, raw_result.get("latency_ms", 0), p_tokens, c_tokens)

                # Final Answer check
                if "Final Answer:" in llm_output:
                    final_response = llm_output.split("Final Answer:")[-1].strip()
                    tree.add_final_answer(final_response)
                    break

                # Action check
                action_match = re.search(r"Action:\s*(\w+)\|(.+)", llm_output)
                if action_match:
                    tool_name = action_match.group(1).strip()
                    tool_args = action_match.group(2).split("\n")[0].strip()

                    tree.add_action(tool_name, tool_args)
                    observation = self._execute_tool(tool_name, tool_args)
                    tree.add_observation(observation)

                    current_prompt += f"Action: {tool_name}|{tool_args}\nObservation: {observation}\n"
                    steps += 1
                    continue

                final_response = llm_output if len(llm_output) > 3 else final_response
                break

        except Exception as e:
            tree.mark_error(str(e))
            final_response = f"Agent Error: {str(e)}"

        total_latency = int((time.time() - start_time) * 1000)
        cost = recorder.calculate_cost(self.llm.model_name, total_prompt_tokens, total_completion_tokens)
        tree.finalize(total_latency, total_prompt_tokens + total_completion_tokens, cost)
        trace_logger.end_trace(trace_id)

        # Record metrics
        trace_meta = {
            "mode": "agent", "model": self.llm.model_name, "input": user_input,
            "response": final_response, "latency_ms": total_latency,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "cost_estimate": cost, "steps": steps, "status": "success", "trace_id": trace_id
        }
        recorder.record(trace_meta)

        self.memory.append({"user": user_input, "agent": f"Response: {final_response}"})
        return trace_meta

    def _execute_tool(self, tool_name: str, args: str) -> str:
        if tool_name not in TOOLS_MAPPING: return f"Error: Unknown tool '{tool_name}'."
        try: return TOOLS_MAPPING[tool_name](args)
        except Exception as e: return f"Error: {str(e)}"

    def clear_memory(self):
        self.memory = []
