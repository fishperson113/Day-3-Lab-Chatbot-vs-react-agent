# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Tran Nguyen Anh Thu
- **Student ID**: 2A202600915
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/retail_tool.py`
- **Code Highlights**: 
```
def execute_tool(tool_name: str, args: str) -> str:
    """
    Parse args string và gọi tool tương ứng.
    args format: "arg1|arg2" (pipe-separated)
    """
    parts = [a.strip() for a in args.split("|")]

    if tool_name == "get_order_weight":
        if len(parts) < 1: return "Thiếu order_id."
        return get_order_weight(parts[0])

    elif tool_name == "calculate_shipping":
        if len(parts) < 2: return "Thiếu weight hoặc province."
        try:
            weight = float(parts[0].replace("kg", "").strip())
        except ValueError:
            return f"Weight không hợp lệ: {parts[0]}"
        return calculate_shipping(weight, parts[1])

    elif tool_name == "check_stock":
        if len(parts) < 1: return "Thiếu tên sản phẩm."
        return check_stock(parts[0])
    else:
        return f"Không tìm thấy tool '{tool_name}'."
```
- **Documentation**: Hàm execute_tool đóng vai trò là Execution Gateway trung gian giữa LLM Core và môi trường thực tế. Trong vòng lặp ReAct, khi mô hình ngôn ngữ sinh ra một chuỗi văn bản dạng Action: tool_name|args, bộ Parser của hệ thống sẽ bóc tách tên tool và chuỗi đối số. Hàm execute_tool sẽ nhận các giá trị thô này, thực hiện chuẩn hóa dữ liệu (như cắt khoảng trắng, ép kiểu float cho cân nặng), sau đó gọi hàm tính toán nội bộ (get_order_weight, calculate_shipping, check_stock) và trả về kết quả dưới dạng chuỗi plain-text làm dữ liệu đầu vào cho bước Observation tiếp theo của Agent.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent rơi vào trạng thái vòng lặp vô hạn (Infinite Loop) hoặc không thể dừng để đưa ra câu trả lời cuối cùng cho người dùng khi gặp các câu hỏi tính toán chi phí phức tạp (ví dụ: "Tính tổng phí: xem đơn ORD123 nặng bao nhiêu rồi tính phí ship về Hanoi hộ tôi").
- **Log Source**: `logs/2026-06-01.log` (Sự kiện lỗi logic trong chuỗi hội thoại liên tiếp mà parser không bắt được token dừng).
- **Diagnosis**: 
1. Lỗi định dạng đầu ra (Formatting Error): Mô hình nhỏ chạy cục bộ (Gemma 3 1B) có xu hướng tự động bao bọc từ khóa Action hoặc câu trả lời bằng các dấu backticks markdown (```) khiến bộ lọc Regex Parser mặc định không khớp được cấu trúc quy định.

2. Thiếu Token Kết Thúc rõ ràng: Khi thực thi xong chuỗi tools tuần tự (Chained Tools: lấy cân nặng -> tính phí ship), Agent tiếp tục sinh ra khối suy nghĩ Thought tiếp theo thay vì trả về cấu trúc dừng nghiêm ngặt Final Answer:. Do Parser không nhận diện được cờ dừng, vòng lặp tiếp tục chạy vô tận cho đến khi bị chặn bởi Guardrail cấu hình.
- **Solution**: 
1. Cập nhật lại System Prompt trong hàm get_system_prompt() để ép model xuất văn bản dạng plain-text thuần túy, cấm tuyệt đối sử dụng các ký tự bao bọc mã code (backticks).

2. Thay đổi cấu trúc Action từ dấu ngoặc tiêu chuẩn sang phân tách bằng ký tự pipe (Action: tool_name|arg1|arg2) để mô hình Gemma 3 1B dễ xử lý và phân tách chuỗi ổn định hơn.

3. Bổ sung cơ chế giám sát vòng lặp nghiêm ngặt với tham số max_steps = 5 và ghi nhận nhật ký mã lỗi max_steps_reached làm phương án Fallback an toàn cho hệ thống.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối lệnh `Thought` hoạt động như một vùng tư duy (tương tự như chuỗi suy luận Chain-of-Thought). Thay vì bắt mô hình phải đoán mò ngay kết quả cuối cùng giống như Chatbot baseline (dễ hallucinate), `Thought` ép agent tự chia nhỏ câu hỏi phức tạp thành các bước đi logic. Nhờ viết ra suy nghĩ trước, agent biết rõ hệ thống đang có dữ liệu gì và đang thiếu thông tin gì để chủ động ra quyết định call tools phù hợp.
2.  **Reliability**: Agent sẽ hoạt động kém hiệu quả và "tốn tài nguyên" hơn Chatbot trong các tác vụ đơn giản như smalltalk, FAQs, hoặc single-step tasks. Việc kích hoạt một vòng lặp ReAct cho các câu hỏi dễ là một sự lãng phí lớn, làm tốn chi phí token và đẩy độ trễ phản hồi (Latency P99) lên rất cao mà không cần thiết.
3.  **Observation**: Kết quả trả về từ Observation đóng vai trò là bằng chứng thực tế nạp vào ngữ cảnh của mô hình cho bước tiếp theo. Nếu tools trả về lỗi (ví dụ: "Không tìm thấy đơn hàng"), agent sẽ nhìn vào đó để bẻ lái hướng đi (như đổi từ khóa tìm kiếm hoặc dừng lại báo lỗi chính xác) thay vì tự bịa ra thông tin.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Tách biệt các logic gọi tools ra một module độc lập tên là ToolManager. Khi hệ thống có hàng ngàn khách hàng dùng cùng lúc, áp dụng lập trình bất đồng bộ để các lượt gọi tools không phải xếp hàng chờ nhau, gây nghẽn hệ thống.
- **Safety**: Thiết lập một Guardrails chặt để kiểm tra kỹ các tham số người dùng nhập vào trước khi truyền vào tool (ví dụ: kiểm tra mã đơn hàng có đúng format không), chặn nguy cơ tấn công phá hoại hệ thống.
- **Performance**: Khi công ty mở rộng lên hàng trăm tools, việc nạp hết tools description vào System Prompt sẽ làm model bị nhiễu và tràn context. Giải pháp nên xem xét là dùng Vector DB để tìm kiếm ngữ nghĩa, chỉ chủ động "gợi ý" Top 3 tools phù hợp nhất với câu hỏi của khách hàng vào Prompt.

---


