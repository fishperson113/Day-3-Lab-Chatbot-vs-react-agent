import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.retail_tools import TOOLS_MAPPING

class ReActAgent:
    """
    ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""Bạn là trợ lý bán lẻ thông minh. Bạn có các công cụ sau:

{tool_descriptions}

Hãy sử dụng đúng định dạng sau:
Thought: suy nghĩ về bước tiếp theo
Action: ten_tool(doi_so)
Observation: kết quả từ tool (hệ thống cung cấp)
... (lặp lại nếu cần thêm thông tin)
Final Answer: câu trả lời cuối cùng

Quy tắc:
- Luôn bắt đầu bằng Thought
- Chỉ gọi 1 Action mỗi bước
- Kết thúc bằng Final Answer khi đã đủ thông tin"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        current_prompt = user_input
        steps = 0
        self.history = []

        while steps < self.max_steps:
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            text = result["content"]

            logger.log_event("AGENT_STEP", {
                "step": steps + 1,
                "output": text,
                "latency_ms": result.get("latency_ms", 0),
                "tokens": result.get("usage", {})
            })

            if "Final Answer:" in text:
                final = text.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "result": final})
                return final

            action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", text, re.DOTALL)
            if action_match:
                tool_name = action_match.group(1).strip()
                args = action_match.group(2).strip()
                observation = self._execute_tool(tool_name, args)

                logger.log_event("TOOL_CALL", {
                    "tool": tool_name,
                    "args": args,
                    "observation": observation
                })

                self.history.append({"step": steps + 1, "tool": tool_name, "args": args, "observation": observation})
                current_prompt += f"\n{text}\nObservation: {observation}"
            else:
                logger.log_event("AGENT_END", {"steps": steps + 1, "result": text})
                return text

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        return "Đã đạt giới hạn bước suy luận. Không tìm được câu trả lời hoàn chỉnh."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        if tool_name not in TOOLS_MAPPING:
            return f"Tool '{tool_name}' không tồn tại."
        try:
            arg_list = []
            for a in args.split(","):
                a = a.strip()
                try:
                    arg_list.append(float(a))
                except ValueError:
                    arg_list.append(a)
            if len(arg_list) == 1:
                return TOOLS_MAPPING[tool_name](arg_list[0])
            return TOOLS_MAPPING[tool_name](*arg_list)
        except Exception as e:
            logger.error(f"Tool error: {str(e)}")
            return f"Lỗi khi gọi tool: {str(e)}"
