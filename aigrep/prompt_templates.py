""" Prompt templates

This is kind of a Wild West right now,
so we need to use some heuristics here.

"""

LLAMA = '''\
<s>[INST] <<SYS>>
{system}
<</SYS>>

{instruction} [/INST]\
'''

VICUNA = '''\
{system}
USER: {instruction}
ASSISTANT:\
'''

WIZARDLM = '''\
{system}

### Instruction:
{instruction}

### Response:\
'''

# Mapping from model ID to their default prompt template.
# It contains only HuggingFace model IDs, currently.
# Author and model names are in alphabetical order.
# Add more as needed, then please contribute them as a PR.
MAPPING = {
    'jondurbin/airoboros-l2-7b-2.2': VICUNA,
    'jondurbin/airoboros-l2-13b-2.2': VICUNA,
    'jondurbin/airoboros-c34b-2.2': VICUNA,

    'meta-llama/Llama-2-7b-hf': LLAMA,
    'meta-llama/Llama-2-13b-hf': LLAMA,
    'meta-llama/Llama-2-70b-hf': LLAMA,
    'meta-llama/Llama-2-7b-chat-hf': LLAMA,
    'meta-llama/Llama-2-13b-chat-hf': LLAMA,
    'meta-llama/Llama-2-70b-chat-hf': LLAMA,

    'WizardLM/WizardCoder-Python-7B-V1.0': WIZARDLM,
    'WizardLM/WizardCoder-Python-13B-V1.0': WIZARDLM,
    'WizardLM/WizardCoder-Python-34B-V1.0': WIZARDLM,
}
