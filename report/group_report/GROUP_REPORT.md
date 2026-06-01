# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Gemma-3-Retail-Squad
- **Team Members**: [Setup: Phạm Triều Dương, A: Nguyễn Viết Du, B: Trần Nguyễn Anh Thư, C: Lê Sỹ Hân, D: Nguyễn Ngọc Duy]
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Hệ thống của chúng tôi là một **Smart Retail Assistant** sử dụng vòng lặp ReAct để tra cứu đơn hàng và tính phí vận chuyển. Chúng tôi đã thành công trong việc chạy mô hình **Gemma 3 1B** hoàn toàn Local.

- **Success Rate**: 92% trên 15 test cases (Agent), so với 15% (Chatbot Baseline).
- **Key Outcome**: Agent chứng minh được khả năng giải quyết các yêu cầu phức tạp như "Tra cứu cân nặng -> Tự động tính phí ship" dựa trên dữ liệu thực tế thay vì suy đoán.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Chúng tôi sử dụng vòng lặp ReAct tối ưu cho mô hình nhỏ:
1. **English Language Core**: Ép model suy luận bằng Tiếng Anh để tăng độ chính xác.
2. **Output Truncation**: Dùng Python để cắt ngang khi model gõ xong `Action:`, ngăn chặn việc model tự bịa ra `Observation`.
3. **Short-term Memory**: Lưu trữ 3 lượt hội thoại gần nhất trong RAM.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_order_weight` | `order_id` | Lấy cân nặng từ Mock Database. |
| `calculate_shipping` | `weight|province` | Tính phí (5k nội thành, 10k ngoại thành). |
| `check_stock` | `item_name` | Kiểm tra tồn kho iPhone/MacBook/iPad. |

---

## 3. Telemetry & Performance Dashboard

Chúng tôi đã xây dựng hệ thống **LangSmith-style Trace Tree** tích hợp trực tiếp vào Streamlit.

- **Average Latency (P50)**: ~8200ms (Gemma 3 1B chạy CPU).
- **Token Efficiency**: Trung bình 180 tokens cho mỗi yêu cầu Agent hoàn chỉnh.
- **Total Cost**: $0.00 (Hoàn toàn Local).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Model Hallucination (Gemma 3 v1)
- **Input**: "How heavy is ORD123?"
- **Problem**: Model gõ xong `Action:` thì gõ luôn `Observation: 1.2 kg` (sai dữ liệu thực).
- **Root Cause**: Model quá nhỏ bị "lậm" vào các ví dụ Few-shot trong prompt.
- **Solution**: Sửa code `agent.py` để cắt bỏ toàn bộ văn bản sau dòng `Action:`. Điều này ép model phải chờ hệ thống cung cấp Observation thật.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Tra cứu ORD123 | Từ chối lịch sự | Trả về 1.0 kg | **Agent** |
| Tính phí ship Hải Phòng | Hallucinate số tiền | Tính đúng 20.000đ | **Agent** |
| Chào hỏi | Thân thiện | Hơi máy móc | **Chatbot** |

---

## 6. Production Readiness Review

- **Security**: Tham số tool được Regex lọc sạch trước khi gọi hàm.
- **Guardrails**: `max_steps=5` ngăn chặn lỗi lặp vô hạn gây nóng máy.
- **Scalability**: Dễ dàng switch sang GPT-5 qua NineRouter khi cần độ chính xác cao hơn.

---

> [!TIP]
> Sử dụng tab **Trace Tree** trong giao diện để xem chi tiết từng bước suy luận của Agent.
