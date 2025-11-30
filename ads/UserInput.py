# input_handler.py
import sys

class UserInput:

    def get_input(self):
        if len(sys.argv) > 2 and sys.argv[1] == "--recover":
            filepath = sys.argv[2]
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return content, True
        else:
            print("Enter your task:")
            prompt = sys.stdin.read().strip()
            return prompt or "No task provided", False
