import argparse
import sys
from pathlib import Path
from typing import Tuple
# ... from tools.loader import load_context_from_file

# Assuming load_context_from_file is defined elsewhere; if not, implement it.
# For example:
# def load_context_from_file(file_path: str) -> str:
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return f.read().strip()
#     except FileNotFoundError:
#         print(f"Error: Recovery file '{file_path}' not found.", file=sys.stderr)
#         sys.exit(1)
#     except Exception as e:
#         print(f"Error loading recovery file: {e}", file=sys.stderr)
#         sys.exit(1)
from ParametersONE import ParametersONE
from tools.loader import ConversationContext

class UserInputHandler:
    """
    Handles user input from command line, either as a prompt or recovery file.

    Usage:
        handler = UserInputHandler()
        input_data, is_recovery = handler.get_input()
    """

    def __init__(self):
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            description=ParametersONE.agentDescription,  #  "AgentONE - Create novels, books, and short stories",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
        Examples:
          # Fresh start with inline prompt
          python kimi-writer.py "Create a collection of sci-fi short stories"
        
          # Recovery mode from previous context
          python kimi-writer.py --recover my_project/.context_summary_20250107_143022.md
                    """
        )

        parser.add_argument(
            'prompt',
            nargs='?',
            default=None,
            help='Your writing request (e.g., "Create a mystery novel")'
        )
        parser.add_argument(
            '--recover',
            type=str,
            default=None,
            help='Path to a context summary file to continue from'
        )

        return parser

    def _handle_recovery(self, recover_path: str) -> Tuple[str, bool]:
        file_path = Path(recover_path)
        if not file_path.exists():
            print(f"Error: Recovery file '{recover_path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        if not file_path.is_file():
            print(f"Error: '{recover_path}' is not a file.", file=sys.stderr)
            sys.exit(1)
        # context = load_context_from_file(str(file_path))
        context = ConversationContext(str(file_path))
        print(context)

        if not context:
            print("Error: Recovery file is empty.", file=sys.stderr)
            sys.exit(1)
        return context, True

    def _handle_prompt_arg(self, prompt: str) -> Tuple[str, bool]:
        prompt_stripped = prompt.strip()
        if not prompt_stripped:
            print("Error: Provided prompt is empty.", file=sys.stderr)
            sys.exit(1)
        return prompt_stripped, False

    def _get_interactive_prompt(self) -> Tuple[str, bool]:
        print("=" * 60)
        print("Granaria AgentONE")
        print("=" * 60)
        print("\nEnter your writing request (or 'quit' to exit):")
        print("Example: Create a collection of 15 sci-fi short stories\n")

        while True:
            prompt = input("> ").strip()

            if prompt.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                sys.exit(0)

            if prompt:
                return prompt, False

            print("Error: Empty prompt. Please provide a writing request or 'quit' to exit.", file=sys.stderr)

    def get_input(self) -> Tuple[str, bool]:
        """
        Gets user input from command line, either as a prompt or recovery file.

        Returns:
            Tuple of (prompt/context, is_recovery_mode)
        """
        args = self.parser.parse_args()

        # Validate arguments: cannot provide both prompt and --recover
        if args.prompt is not None and args.recover is not None:
            self.parser.error("Error: Cannot provide both a prompt and --recover. Use one or the other.")

        # Check if recovery mode
        if args.recover:
            return self._handle_recovery(args.recover)

        # Check if prompt provided as argument
        if args.prompt is not None:
            return self._handle_prompt_arg(args.prompt)

        # Interactive prompt
        return self._get_interactive_prompt()



if __name__ == "__main__":
    # Example usage for testing
    handler = UserInputHandler()
    input_data, is_recovery = handler.get_input()
    print(f"Input: {input_data}")
    print(f"Recovery mode: {is_recovery}")