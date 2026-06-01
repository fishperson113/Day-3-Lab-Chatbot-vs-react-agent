# 🧪 Kịch bản Test: Chatbot vs ReAct Agent (Retail Use Case)

Sử dụng bộ test này để so sánh khả năng của **Chatbot Baseline** và **ReAct Agent** (sử dụng model Gemma 3 1B).

---

## 📋 Dữ liệu mẫu (MOCK) trong hệ thống
Để đối chiếu kết quả, đây là dữ liệu thật đang nằm trong code (`retail_tools.py`):
- **Đơn hàng ORD123**: Nặng 1.0 kg, ở Hanoi.
- **Đơn hàng ORD456**: Nặng 2.0 kg, ở HCM.
- **Kho hàng**: iPhone (10 cái), MacBook (5 cái), **iPad (0 cái - Hết hàng)**.
- **Phí ship**: Nội thành (Hanoi, HCM) = 5.000đ/kg | Ngoại thành = 10.000đ/kg.

---

## 🎯 Bộ câu hỏi Test

### Loại 1: Tra cứu thông tin đơn lẻ (Single-hop)
**Câu hỏi:** `Đơn hàng ORD123 nặng bao nhiêu kg?`
- **Chatbot**: Thường sẽ trả lời "Tôi không biết" hoặc bịa ra một con số.
- **Agent**: Phải gọi `get_order_weight|ORD123` và trả về đúng `1.0 kg`.

### Loại 2: Suy luận nhiều bước (Multi-hop)
**Câu hỏi:** `Tính tổng phí ship về Hải Phòng cho đơn hàng ORD456.`
- **Chatbot**: Sẽ gặp khó khăn vì không biết cân nặng của ORD456.
- **Agent**: 
    1. Bước 1: `get_order_weight|ORD456` -> Lấy được `2.0 kg`.
    2. Bước 2: `calculate_shipping|2.0|Hai Phong` -> Tính ra `20000 VND`.
    3. Kết luận: Tổng phí là 20.000 VNĐ.

### Loại 3: Kiểm tra điều kiện & Hết hàng (Logic)
**Câu hỏi:** `Tôi muốn mua iPad, shop còn hàng không?`
- **Chatbot**: Dễ bị "ảo tưởng" (Hallucination) trả lời là còn hàng để chiều lòng khách.
- **Agent**: 
    1. Bước 1: `check_stock|ipad` -> Nhận kết quả `Còn 0 cái`.
    2. Kết luận: Trả lời khách là đã hết hàng.

### Loại 4: Câu hỏi không liên quan (Out of Domain)
**Câu hỏi:** `Thời tiết hôm nay ở Sài Gòn thế nào?`
- **Cả 2**: Đều không có tool thời tiết nên sẽ trả lời dựa trên kiến thức chung hoặc từ chối. (Dùng để test xem Agent có bị "ngáo" mà gọi nhầm tool bán hàng không).

---

## 🚀 Cách thực hiện Test

1. **Mở Terminal 1 (Chatbot):**
   ```bash
   uv run main.py chatbot
   ```
2. **Mở Terminal 2 (Agent):**
   ```bash
   uv run main.py agent
   ```
3. **Copy-paste** từng câu hỏi trên vào cả 2 terminal.
4. **Ghi lại kết quả**: 
   - Chatbot có bịa số không?
   - Agent có đi đúng các bước `Thought -> Action -> Observation` không?
   - Latency (thời gian phản hồi) bên nào nhanh hơn? (Thường chatbot nhanh hơn nhưng agent chính xác hơn).

---
*Lưu ý: Nếu Agent gặp lỗi "Max steps reached", hãy kiểm tra lại format trong log hoặc thử diễn đạt câu hỏi rõ ràng hơn.*
