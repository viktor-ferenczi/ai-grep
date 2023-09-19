#!/usr/bin/python3
import asyncio
import os.path
import sys
from typing import Tuple

from aigrep.config import Config, DEFAULT_CONFIG, ModelConfig
from aigrep.model import Model
from aigrep.processor import Processor
from arguments import create_argument_parser, ArgsNamespace


def load_config(args: ArgsNamespace) -> Tuple[str, Config]:
    path = args.config or '~/.aigrep/config.toml'
    path = os.path.expanduser(path) if path else ''

    if path and os.path.exists(path):
        return path, Config.load(path)

    return path, DEFAULT_CONFIG


def load_model(args, cfg: ModelConfig):
    cfg = cfg.clone()

    if args.window is not None:
        cfg.window = args.window

    if args.parallel is not None:
        cfg.parallel = args.parallel

    if args.temperature is not None:
        cfg.temperature = args.temperature

    model = Model(cfg)
    return model


async def run(args: ArgsNamespace):
    path, config = load_config(args)

    if args.info:
        for cfg in config.models:
            print(cfg.id)
        return

    if args.write:
        if os.path.exists(path):
            print(f'Already exists: {path}')
        else:
            DEFAULT_CONFIG.save(path)
            print(f'Wrote: {path}')
        return

    for cfg in config.models:
        if args.model is None or cfg.id == args.model:
            break
    else:
        print(f'No model configured with ID: {args.model}')
        sys.exit(1)

    model = load_model(args, cfg)

    if args.test:
        if not asyncio.run(model.test()):
            print('FAILED')
            sys.exit(1)
        print('OK')
        return

    processor = Processor(args, config, model)
    if not await processor.process():
        sys.exit(1)


def main():
    argument_parser = create_argument_parser()
    # noinspection PyTypeChecker
    args: ArgsNamespace = argument_parser.parse_args(sys.argv[1:])
    asyncio.run(run(args))


if __name__ == '__main__':
    main()
