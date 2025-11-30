# client.py
import os
import sys

from openai import OpenAI
# from ParametersONE import API_KEY, BASE_URL  # , MODEL
from ParametersONE import ParametersONE

class MoonshotClient:
    def __init__(self):
        _a_KEY = os.getenv("MOONSHOT_API_KEY")
        if not _a_KEY:
            print("Error: MOONSHOT_API_KEY environment variable not set.")
            print("Please set your API key: export MOONSHOT_API_KEY='your-key-here'")
            sys.exit(1)
        print("\nMoonshotClient execution finished!")
        print(_a_KEY)

        self.api_key = _a_KEY
        if len(_a_KEY) > 8:
            print(f"✓ API Key loaded: {_a_KEY[:4]}...{_a_KEY[-4:]}")
        else:
            print(f"⚠️ Warning: API key seems too short ({len(_a_KEY)} chars)")


        _b_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
        if not _b_URL:
            print("Error: MOONSHOT_BASE_URL environment variable not set.")
            sys.exit(1)
        print(f"✓ Base URL: {_b_URL}\n")

        self.base_url = _b_URL
        self.client = OpenAI(api_key=_a_KEY, base_url=_b_URL)
        self.model = ParametersONE.MODEL



    def chat_completion(self, messages, tools, stream=True):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or [],
            max_tokens=ParametersONE.MAX_TOKENS,
            temperature=1.0,
            stream=stream,
        )