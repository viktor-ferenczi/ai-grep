import os
from dataclasses import dataclass, asdict
from typing import List, Union, Optional, Dict, Any

import toml

from aigrep.prompt_templates import MAPPING


@dataclass
class ModelConfig:
    # Model, currently a HuggingFace ID
    id: str

    # LLM engine
    provider: str = 'vllm'
    address: str = 'http://127.0.0.1:8000/generate'

    # Context window size
    context: int = 4096

    # Maximum number of parallel generations
    parallel: int = 32

    # Sampling parameters
    best_of: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = -1
    use_beam_search: bool = False
    length_penalty: float = 1.0
    early_stopping: Union[bool, str] = False
    stop: Union[None, str, List[str]] = None
    ignore_eos: bool = False

    @property
    def prompt_template(self) -> str:
        return MAPPING[self.id]

    @property
    def sampling_params_dict(self) -> Dict[str, Any]:
        return dict(
            best_of=self.best_of,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            use_beam_search=self.use_beam_search,
            length_penalty=self.length_penalty,
            early_stopping=self.early_stopping,
            stop=self.stop,
            ignore_eos=self.ignore_eos,
        )

    def clone(self):
        return ModelConfig(**asdict(self))

    @classmethod
    def from_data(cls, data: dict) -> "ModelConfig":
        return cls(**data)


@dataclass
class Config:
    models: List[ModelConfig]

    def clone(self):
        return Config(
            models=[m.clone() for m in self.models]
        )

    @classmethod
    def from_data(cls, data: dict) -> "Config":
        return cls(
            models=[
                ModelConfig.from_data(item)
                for item in data.get('models', [])
            ]
        )

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wt', encoding='utf-8') as f:
            toml.dump(asdict(self), f)

    @classmethod
    def load(cls, path: str) -> "Config":
        with open(path, 'rt', encoding='utf-8') as f:
            data = toml.load(f)
        return cls.from_data(data)


DEFAULT_CONFIG = Config(
    [
        ModelConfig(
            id='WizardLM/WizardCoder-Python-13B-V1.0',
            context=4096,
            parallel=32,
            best_of=None,
            presence_penalty=0.0,
            frequency_penalty=0.2,
            temperature=0.5,
            top_p=1.0,
            top_k=-1,
            use_beam_search=False,
            length_penalty=1.0,
            early_stopping=False,
            stop=None,
            ignore_eos=False,
        ),
    ]
)
