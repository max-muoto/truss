import os
from dataclasses import asdict, dataclass
from typing import Any, Dict

from ctransformers import AutoConfig, AutoModelForCausalLM


@dataclass
class GenerationConfig:
    temperature: float
    top_k: int
    top_p: float
    repetition_penalty: float
    max_new_tokens: int
    seed: int
    reset: bool
    stream: bool
    threads: int
    stop: list[str]


def format_prompt(user_prompt: str):
    return f"""### Instruction:
{user_prompt}

### Response:"""


def generate(
    llm: AutoModelForCausalLM,
    generation_config: GenerationConfig,
    user_prompt: str,
):
    """run model inference, will return a Generator if streaming is true"""

    return llm(
        format_prompt(
            user_prompt,
        ),
        **asdict(generation_config),
    )


class Model:
    def __init__(self, **kwargs) -> None:
        self._data_dir = kwargs["data_dir"]
        self._config = kwargs["config"]
        self._secrets = kwargs["secrets"]
        self._llm = None
        self._model_config = None

    def load(self):
        self._model_config = AutoConfig.from_pretrained(
            str(self._data_dir / "configs"), context_length=2048
        )

        # IMPORTANT: in order to load the LM's weights, create a `models` directory in the `data`` folder
        # and move `replit-v2-codeinstruct-3b.q4_1.bin` into it.
        self._llm = AutoModelForCausalLM.from_pretrained(
            str(self._data_dir / "models"), model_type="replit"
        )

    def predict(self, model_input: Dict) -> Any:
        generation_config = GenerationConfig(
            temperature=0.2,
            top_k=50,
            top_p=0.9,
            repetition_penalty=1.0,
            max_new_tokens=512,  # adjust as needed
            seed=42,
            reset=True,  # reset history (cache)
            stream=True,  # streaming per word/token
            threads=int(os.cpu_count() / 6),  # adjust for your CPU
            stop=["<|endoftext|>"],
        )
        user_prompt = model_input.pop("prompt")
        generator = generate(self._llm, generation_config, user_prompt.strip())
        result = ""
        for word in generator:
            result += word
        return result
