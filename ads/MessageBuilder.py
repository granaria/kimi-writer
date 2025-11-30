# messages.py
from typing import List, Dict, Any
import json

class MessageBuilder:
    @staticmethod
    def from_stream():
        return {
            "content": "",
            "reasoning_content": "",
            "tool_calls": [],
            "role": "assistant"
        }

    @staticmethod
    def finalize(accumulated: dict) -> Dict[str, Any]:
        msg = {"role": "assistant"}
        if accumulated["content"]:
            msg["content"] = accumulated["content"]
        if accumulated["reasoning_content"]:
            msg["reasoning_content"] = accumulated["reasoning_content"]
        if accumulated["tool_calls"]:
            msg["tool_calls"] = accumulated["tool_calls"]
            msg["content"] = None  # OpenAI spec: content=null when tool_calls present
        return msg