import os
import sys
import html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Make the local src package importable
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from src.chatbot import SimpleChatbot
from src.agent.agent import ReActAgent
from src.tools.retail_tools import TOOLS_MAPPING
from src.core.hf_provider import HFProvider

AVAILABLE_PROVIDERS = ["hf", "local", "openai", "gemini"]
AVAILABLE_MODES = ["chatbot", "agent"]

TOOLS = [
    {"name": "get_order_weight", "description": "Lấy cân nặng đơn hàng", "function": TOOLS_MAPPING["get_order_weight"]},
    {"name": "calculate_shipping", "description": "Tính phí ship", "function": TOOLS_MAPPING["calculate_shipping"]},
    {"name": "check_stock", "description": "Kiểm tra tồn kho", "function": TOOLS_MAPPING["check_stock"]}
]

APP_STATE = {
    "provider": None,
    "mode": None,
    "worker": None,
    "history": []
}


def html_escape(text: str) -> str:
    return html.escape(text, quote=True)


def render_template(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{html_escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 24px auto; line-height: 1.6; }}
    textarea {{ width: 100%; min-height: 120px; }}
    select, input[type=text] {{ width: 100%; padding: 8px; margin-top: 4px; margin-bottom: 12px; }}
    button {{ padding: 10px 16px; margin-top: 8px; }}
    pre {{ background: #f5f5f5; padding: 16px; white-space: pre-wrap; word-break: break-word; }}
    .section {{ margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h1>{html_escape(title)}</h1>
  {body}
</body>
</html>"""


def build_provider(provider_name: str, local_model_path: str | None = None):
    provider = provider_name.lower()
    if provider == "hf":
        return HFProvider(model_id=os.getenv("HF_MODEL_ID", "google/gemma-3-1b-it"))

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

    if provider == "gemini":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=os.getenv("GOOGLE_API_KEY"))

    if provider == "local":
        from src.core.local_provider import LocalProvider
        model_path = local_model_path or os.getenv("LOCAL_MODEL_PATH")
        if not model_path:
            raise ValueError("Local model path is required for the local provider.")
        return LocalProvider(model_path=model_path)

    raise ValueError(f"Unknown provider '{provider_name}'")


def build_worker(mode: str, llm):
    if mode == "agent":
        return ReActAgent(llm=llm, tools=TOOLS)
    return SimpleChatbot(llm=llm)


def render_selection_page(message: str = "") -> str:
    options_html = "".join(
        f"<option value=\"{p}\">{p.upper()}</option>" for p in AVAILABLE_PROVIDERS
    )
    mode_options_html = "".join(
        f"<option value=\"{m}\">{m.title()}</option>" for m in AVAILABLE_MODES
    )
    return render_template(
        "Agent Interface Configuration",
        f"""
<div class=\"section\">
  <p>Choose one provider and one mode. The selected model will load only after you submit this form.</p>
  {f'<p style=\"color: red;\">{html_escape(message)}</p>' if message else ''}
</div>
<form method=\"post\" action=\"/configure\">
  <div class=\"section\">
    <label>Provider</label>
    <select name=\"provider\">{options_html}</select>
  </div>
  <div class=\"section\">
    <label>Mode</label>
    <select name=\"mode\">{mode_options_html}</select>
  </div>
  <div class=\"section\">
    <label>Local model path (.gguf) - only needed for local provider</label>
    <input type=\"text\" name=\"local_model_path\" placeholder=\"/path/to/model.gguf\" />
  </div>
  <button type=\"submit\">Start Session</button>
</form>
"""
    )


def render_chat_page():
    provider = APP_STATE["provider"]
    mode = APP_STATE["mode"]
    history_items = "".join(
        f"<div><strong>You:</strong> {html_escape(item['question'])}</div>"
        f"<div><strong>AI:</strong> {html_escape(item['response'])}</div>"
        f"<div style=\"color: #666; margin-bottom: 12px;\">Latency: {item.get('latency_ms', 'n/a')} ms</div>"
        for item in APP_STATE["history"]
    )
    return render_template(
        "Agent Interface Chat",
        f"""
<div class=\"section\">
  <p>Provider: <strong>{html_escape(provider)}</strong></p>
  <p>Mode: <strong>{html_escape(mode)}</strong></p>
</div>
<form method=\"post\" action=\"/chat\">
  <div class=\"section\">
    <label>Message to the AI</label>
    <textarea name=\"message\"></textarea>
  </div>
  <button type=\"submit\">Send</button>
</form>
<form method=\"post\" action=\"/reset\">
  <button type=\"submit\">Reset Session</button>
</form>
<div class=\"section\">
  <h2>Conversation</h2>
  {history_items if history_items else '<p>No messages yet.</p>'}
</div>
"""
    )


def build_error_page(error: str) -> str:
    return render_template(
        "Agent Interface Error",
        f"<div class=\"section\"><p style=\"color:red;\">{html_escape(error)}</p></div>"
    )


class InterfaceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        page = render_chat_page() if APP_STATE["worker"] else render_selection_page()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = {k: v[0] for k, v in parse_qs(body).items()}

        if self.path == "/configure":
            self.handle_configure(params)
            return

        if self.path == "/chat":
            self.handle_chat(params)
            return

        if self.path == "/reset":
            self.handle_reset()
            return

        self.send_error(404)

    def handle_configure(self, params: dict):
        provider = params.get("provider", "").strip().lower()
        mode = params.get("mode", "").strip().lower()
        local_model_path = params.get("local_model_path", "").strip() or None

        if provider not in AVAILABLE_PROVIDERS:
            self.respond_html(render_selection_page("Invalid provider selected."))
            return

        if mode not in AVAILABLE_MODES:
            self.respond_html(render_selection_page("Invalid mode selected."))
            return

        try:
            llm = build_provider(provider, local_model_path)
            worker = build_worker(mode, llm)
        except Exception as exc:
            self.respond_html(render_selection_page(str(exc)))
            return

        APP_STATE["provider"] = provider
        APP_STATE["mode"] = mode
        APP_STATE["worker"] = worker
        APP_STATE["history"] = []

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def handle_chat(self, params: dict):
        if APP_STATE["worker"] is None:
            self.respond_html(render_selection_page("Please configure a provider and mode first."))
            return

        message = params.get("message", "").strip()
        if not message:
            self.respond_html(render_chat_page())
            return

        try:
            raw_response = APP_STATE["worker"].run(message)
            response_text = raw_response.get("response") if isinstance(raw_response, dict) else str(raw_response)
            latency = raw_response.get("latency_ms") if isinstance(raw_response, dict) else None
            APP_STATE["history"].append({
                "question": message,
                "response": response_text,
                "latency_ms": latency,
            })
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        except Exception as exc:
            self.respond_html(build_error_page(str(exc)))

    def handle_reset(self):
        APP_STATE["provider"] = None
        APP_STATE["mode"] = None
        APP_STATE["worker"] = None
        APP_STATE["history"] = []
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def respond_html(self, html_text: str):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_text.encode("utf-8"))


def run_server(host: str = "127.0.0.1", port: int = 8080):
    server_address = (host, port)
    httpd = HTTPServer(server_address, InterfaceHandler)

    print(f"Agent interface is available at http://{host}:{port}")
    print("Open the page in your browser, choose provider and mode, then send one prompt at a time.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down interface server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
