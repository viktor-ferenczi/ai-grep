from typing import List, Tuple

from vllm_client.async_client import AsyncVllmClient
from vllm_client.sampling_params import SamplingParams

from aigrep.config import ModelConfig
from aigrep.utils import count_tokens


class Model:

    def __init__(self, cfg: ModelConfig):
        self.cfg: ModelConfig = cfg

        assert cfg.id, 'Unspecified model id'
        assert cfg.provider, 'Unspecified model provider'
        assert cfg.address, 'Unspecified model address'
        assert cfg.context > 0, f'Invalid context size: {cfg.context}'
        assert cfg.parallel > 0, f'Invalid parallelism: {cfg.parallel}'

        if cfg.provider == 'vllm':
            self.client = AsyncVllmClient(cfg.address)
        else:
            raise ValueError(f'Unknown model provider: {cfg.provider}')

    async def generate(self, system: str, instruction: str, params: SamplingParams) -> List[Tuple[str, int]]:
        prompt = self.cfg.prompt_template.format(system=system, instruction=instruction)

        def fn(output) -> Tuple[str, int]:
            generated = output[len(prompt):]
            return generated, count_tokens(output)

        return [fn(output) for output in await self.client.generate(prompt, params)]

    async def test(self) -> bool:
        outputs: List[Tuple[str, int]] = await self.generate(
            'You are a helpful assistant.',
            'You are a math student. What is the area of a unit square?',
            SamplingParams(**self.cfg.sampling_params_dict))

        if len(outputs) != 1:
            print('Wrong number of outputs')
            return False

        output, cost = outputs[0]

        if '1' not in output and 'one' not in output.lower():
            print(f'Unexpected output: {outputs!r}')
            return False

        if cost < count_tokens(output):
            print(f'Unexpected cost: {outputs!r}')
            return False

        return True
