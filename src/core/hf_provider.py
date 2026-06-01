import time
import torch
from typing import Dict, Any, Optional, Generator
from transformers import AutoTokenizer, AutoModelForCausalLM
from src.core.llm_provider import LLMProvider

class HFProvider(LLMProvider):
    """
    LLM Provider using Hugging Face Transformers.
    Downloads and caches models automatically.
    """
    def __init__(self, model_id: str = "google/gemma-3-1b-it"):
        super().__init__(model_name=model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Load in 4-bit if possible, or just normal for 1B
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False # For deterministic ReAct results
            )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Extract only the new tokens
        input_length = inputs["input_ids"].shape[-1]
        content = self.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)

        usage = {
            "prompt_tokens": input_length,
            "completion_tokens": len(outputs[0]) - input_length,
            "total_tokens": len(outputs[0])
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "huggingface"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        # Simple non-streaming wrapper for HF for now
        # Proper streaming requires TextIteratorStreamer
        result = self.generate(prompt, system_prompt)
        yield result["content"]
