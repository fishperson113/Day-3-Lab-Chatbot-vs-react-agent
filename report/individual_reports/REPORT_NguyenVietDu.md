# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Viết Du
- **Student ID**: [2A202600800]
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `src/agent/agent.py`
- **Code Highlights**:

  **ReAct Loop — `run()` method:**
  ```python
  while steps < self.max_steps:
      result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
      text = result["content"]
      if "Final Answer:" in text:
          return text.split("Final Answer:")[-1].strip()
      action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", text, re.DOTALL)
      if action_match:
          observation = self._execute_tool(tool_name, args)
          current_prompt += f"\n{text}\nObservation: {observation}"
  ```

  **Tool Execution — `_execute_tool()` method:**
  ```python
  def _execute_tool(self, tool_name: str, args: str) -> str:
      arg_list = []
      for a in args.split(","):
          a = a.strip()
          try:
              arg_list.append(float(a))
          except ValueError:
              arg_list.append(a)
      return TOOLS_MAPPING[tool_name](*arg_list)
  ```

- **Documentation**: `ReActAgent.run()` nhận user input, gọi LLM lặp lại theo vòng Thought→Action→Observation cho đến khi LLM output ra `Final Answer:` hoặc đạt `max_steps`. Mỗi bước tool call được ghi log qua `IndustryLogger` để phục vụ phân tích sau.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: [Điền sau khi chạy — ví dụ: Agent không parse được Action vì LLM output sai format]
- **Log Source**: [Dán snippet từ `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Tại sao LLM làm vậy? Prompt chưa đủ ví dụ? Model quá nhỏ?]
- **Solution**: [Sửa system prompt, thêm few-shot example, v.v.]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Khối `Thought` buộc LLM phân rã bài toán thành từng bước nhỏ trước khi hành động — thay vì đoán ngay một lần. Điều này giúp agent xử lý đúng các câu hỏi multi-step như "Đơn ORD123 ship về Hanoi tốn bao nhiêu?" trong khi chatbot chỉ hallucinate con số.

2. **Reliability**: Agent tệ hơn chatbot trong câu hỏi đơn giản vì tốn nhiều bước hơn. Ví dụ "Xin chào" — chatbot trả lời ngay, agent lại cố gọi tool không cần thiết.

3. **Observation**: [Điền sau khi chạy thực tế]

---

## IV. Future Improvements (5 Points)

- **Scalability**: Dùng async tool calls để chạy song song nhiều tool cùng lúc thay vì tuần tự.
- **Safety**: Thêm Supervisor LLM kiểm tra argument trước khi gọi tool — tránh inject qua args.
- **Performance**: Vector DB để retrieve đúng tool khi hệ thống có hàng chục tools, thay vì liệt kê tất cả trong system prompt.

---

> Submitted by Nguyễn Viết Du — `src/agent/agent.py`
