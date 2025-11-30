# tokenizer.py
import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")

def estimate_tokens(messages) -> int:
    """Rough but safe token estimation"""
    total = 0
    for msg in messages:
        for key, value in msg.items():
            if isinstance(value, str):
                total += len(_encoder.encode(value)) + 4
    return int(total * 1.1)  # +10% safety margin