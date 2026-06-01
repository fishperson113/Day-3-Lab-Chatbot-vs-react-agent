# 🚀 Hướng dẫn Cài đặt & Chạy Project (Full Setup Guide)

Tài liệu này hướng dẫn chi tiết cách cấu hình project để chạy với model local (Gemma 3) hoặc API Cloud (OpenAI/NineRouter).

---

## 📦 1. Cài đặt ban đầu (Prerequisites)

Dùng `uv` để quản lý dependencies nhanh chóng:

```bash
# Cài đặt uv nếu chưa có (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Cài đặt dependencies
uv pip install -r requirements.txt
```

---

## 🔋 2. Chạy Localhost với Gemma 3 1B

### Cách A: Dùng `HFProvider` (Cần GPU/RAM lớn)
*Code sử dụng thư viện `transformers` để load model trực tiếp.*

1. **Cấp quyền:** Truy cập [google/gemma-3-1b-it](https://huggingface.co/google/gemma-3-1b-it) và nhấn **Acknowledge license**.
2. **Login:** Lấy token tại [HF Settings](https://huggingface.co/settings/tokens) và chạy:
   ```bash
   uv run huggingface-cli login
   ```
3. **Config `.env`:**
   ```env
   DEFAULT_PROVIDER=hf
   HF_MODEL_ID=google/gemma-3-1b-it
   ```

### Cách B: Dùng `LocalProvider` (Tối ưu CPU - Khuyên dùng)
*Sử dụng `llama-cpp-python` để chạy file `.gguf` nhẹ.*

1. **Tải GGUF:** Tải từ [Gemma-3-1b-it-GGUF](https://huggingface.co/google/gemma-3-1b-it-GGUF) và bỏ vào thư mục `models/`.
2. **Cài đặt thư viện:**
   ```bash
   uv pip install llama-cpp-python
   ```
3. **Cấu hình:** Hiện tại `main.py` đang ưu tiên `HFProvider`. Để dùng `LocalProvider`, bạn cần chỉnh lại code trong `main.py` (hàm `create_worker`).

---

## 🌐 3. Cấu hình OpenAI & Proxy (NineRouter)

Code hiện tại trong `main.py` và `OpenAIProvider` được thiết kế linh hoạt để bạn chọn giữa NineRouter (Proxy) hoặc OpenAI trực tiếp.

### Lựa chọn 1: Dùng NineRouter (Mặc định)
NineRouter là một proxy giúp bạn truy cập nhiều model qua 1 endpoint.
Cấu hình `.env`:
```env
DEFAULT_PROVIDER=openai
NINEROUTER_URL=https://api.ninerouter.com/v1  # Endpoint của proxy
NINEROUTER_KEY=sk-xxx...                     # Key của NineRouter
NINEROUTER_MODEL=openai/gpt-4o               # Model ID trên NineRouter
```

### Lựa chọn 2: Dùng OpenAI trực tiếp (Không qua Proxy)
Nếu bạn có Key OpenAI chính chủ và muốn dùng trực tiếp:
Cấu hình `.env`:
```env
DEFAULT_PROVIDER=openai
NINEROUTER_URL=https://api.openai.com/v1     # Đổi endpoint về OpenAI chính chủ
NINEROUTER_KEY=sk-proj-xxx...                # Key OpenAI của bạn
NINEROUTER_MODEL=gpt-4o                      # Model ID chuẩn của OpenAI
```

---

## 🏃 4. Khởi chạy ứng dụng

Project hỗ trợ 2 giao diện:

### Giao diện Terminal (CLI)
```bash
uv run main.py agent      # Chạy Agent với ReAct loop
uv run main.py chatbot    # Chạy Chatbot đơn giản
```

### Giao diện Web (Streamlit)
```bash
uv run streamlit run interface.py
```

---

## 🛠️ Giải quyết sự cố thường gặp
- **Lỗi `bitsandbytes`:** Xảy ra trên Windows khi chạy `HFProvider`. Giải pháp: Cài đặt bản GGUF và dùng `LocalProvider` (Cách B).
- **Lỗi `401 Unauthorized`:** Kiểm tra lại `NINEROUTER_KEY` hoặc `HF_TOKEN`.
- **Model không trả lời:** Đảm bảo `DEFAULT_PROVIDER` trong `.env` khớp với phần bạn đã cấu hình.
