import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

"""
def load_context_from_file(file_path: str) -> str:
    ""
    Loads context from a summary file for recovery.

    Args:
        file_path: Path to the context summary file

    Returns:
        Content of the file as string
    ""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Loaded context from: {file_path}\n")
        return content
    except Exception as e:
        print(f"✗ Error loading context file: {e}")
        sys.exit(1)

"""



class ConversationContext:
    """
    A simple but robust persistent conversation context manager.
    Perfect for local LLMs, agents, or long-running Grok-style chats.
    """

    DEFAULT_SUMMARY_FILE = "context_summary.txt"


    def __init__(self, summary_file: str | Path = DEFAULT_SUMMARY_FILE):
        self.summary_file = Path(summary_file)
        self.context: str = self._load_existing_context()

    def _load_existing_context(self) -> str:
        """Load previous context on startup (your function, improved)"""
        if not self.summary_file.exists():
            print(f"No previous context found. Starting fresh → {self.summary_file}\n")
            return ""

        try:
            _contxt = self.summary_file.read_text(encoding='utf-8').strip()
            if _contxt:
                print(f"Context recovered from: {self.summary_file.resolve()}\n")
                return _contxt
            else:
                print("Context file was empty. Starting fresh.\n")
                return ""
        except Exception as e:
            print(f"Failed to load context file: {e}")
            sys.exit(1)
    '''
    def update(self, new_summary: str) -> None:
        """Update the current context and write to disk immediately"""
        self.context = new_summary.strip()
        self.save()

    def append(self, addition: str) -> None:
        """Append new information to the existing context"""
        if self.context and not self.context.endswith('\n'):
            self.context += '\n'
        self.context += addition.strip() + '\n'
        self.save()

    def save(self) -> None:
        """Atomically save context with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"# Last updated: {timestamp} (CET)\n\n"

        try:
            self.summary_file.write_text(header + self.context.strip() + '\n', encoding='utf-8')
        except Exception as e:
            print(f"Failed to save context: {e}")
            sys.exit(1)

    def clear(self) -> None:
        """Start completely fresh"""
        self.context = ""
        if self.summary_file.exists():
            self.summary_file.unlink()
        print("Context cleared.\n")

    def __str__(self) -> str:
        return self.context

    def __repr__(self) -> str:
        return f"ConversationContext(file='{self.summary_file}', lines={len(self.context.splitlines())})"
    '''


# Example usage:
if __name__ == "__main__":
    ctx = ConversationContext("my_grk_session.txt")
    print("Current context:")
    print(ctx or "(empty)")

    # Simulate new summary from LLM
    # ctx.update("User is @DrJo from Zurich. Working on persistent AI agents. Loves clean Python code. Current goal: build a never-forgetting local assistant.")