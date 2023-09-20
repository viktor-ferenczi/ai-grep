# FIXME: Use the right tokenizer for the selected model
import json
import mimetypes
from typing import List

import tiktoken

ENCODING = tiktoken.encoding_for_model('gpt-3.5-turbo')


# FIXME: This is a good approximation for now
def count_tokens(text: str) -> int:
    if not text.strip():
        return 0

    tokens: List[int] = ENCODING.encode(
        text,
        disallowed_special=()
    )

    return len(tokens)


def extract_code_block(text: str, format: str) -> str:
    st = text.strip()
    stlc = st.lower()

    for prefix in (f'```{format}', '```'):
        i = stlc.find(prefix)
        j = stlc.rfind('```')
        if 0 <= i < j:
            return st[i + len(prefix):j]

    if st.startswith('`') or st.endswith('`'):
        return st.strip('`')

    return text
