import time
from typing import Dict, Any, Optional, Generator
from openai import OpenAI
from src.core.llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    """
    OpenAI Provider that supports custom Base URL (like NineRouter).
    """
    def __init__(self, model_name: str, api_key: Optional[str], base_url: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url # Inject custom proxy URL
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        content = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "openai_proxy"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        # Implement streaming if needed
        pass
