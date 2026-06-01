import time
import torch
from typing import Dict, Any, Optional, Generator
from transformers import AutoTokenizer, BitsAndBytesConfig, AutoModelForCausalLM
from src.core.llm_provider import LLMProvider

class HFProvider(LLMProvider):
    """
    LLM Provider using Hugging Face Transformers.
    Optimized for Gemma 3 with 8-bit quantization.
    """
    def __init__(self, model_id: str = "google/gemma-3-1b-it"):
        super().__init__(model_name=model_id)

        print(f"Loading model {model_id}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Quantization config for 8-bit (requires bitsandbytes)
        quantization_config = None
        if torch.cuda.is_available():
            try:
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                print("Using 8-bit quantization.")
            except ImportError:
                print("bitsandbytes not found, loading in full precision.")

        # Load model (AutoModelForCausalLM will resolve to Gemma3ForCausalLM)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True
        ).eval()

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        # Format messages for Gemma 3 chat template
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})

        messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

        # Apply template
        inputs = self.tokenizer.apply_chat_template(
            [messages], # Template expects a list of conversations
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.model.device)

        # Generate
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False
            )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Decode output (skipping input tokens)
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
        result = self.generate(prompt, system_prompt)
        yield result["content"]
