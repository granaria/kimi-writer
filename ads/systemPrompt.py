# prompts.py
import os
from typing import Optional, Dict, Any
from pathlib import Path


class SystemPrompt:
    """
    Manages system prompts for AgentONE.
    Supports loading from file, templating, and validation.
    """

    def __init__(
            self,
            prompt_file: Optional[str] = None,
            default_prompt: Optional[str] = None,
            templates: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize with a file path, default string, or both.

        Args:
            prompt_file: Path to .txt file (e.g., 'system_prompt.txt').
            default_prompt: Fallback hardcoded prompt string.
            templates: Dict of placeholders, e.g., {'{model}': 'Moonshot-v1'}.
        """
        self.prompt_file = prompt_file
        self.default_prompt = default_prompt
        self.templates = templates or {}
        self._prompt = None
        self._load_prompt()

    def _load_prompt(self):
        """Load prompt from file or default."""
        if self.prompt_file and os.path.exists(self.prompt_file):
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                self._prompt = f.read().strip()
        elif self.default_prompt:
            self._prompt = self.default_prompt
        else:
            raise ValueError("No prompt provided: Set prompt_file or default_prompt.")

        if not self._prompt:
            raise ValueError("Loaded prompt is empty.")

        # Apply templates
        self._prompt = self._prompt.format(**self.templates)

    @property
    def prompt(self) -> str:
        """Get the resolved prompt."""
        return self._prompt

    def update_templates(self, new_templates: Dict[str, Any]):
        """Update templates and reload."""
        self.templates.update(new_templates)
        self._load_prompt()

    def validate(self) -> bool:
        """Basic validation: Check length and key elements."""
        if len(self.prompt) < 50:
            return False  # Too short
        if "AgentONE" not in self.prompt and "system" not in self.prompt.lower():
            print("Warning: Prompt may lack agent identity.")
        return True

    @staticmethod
    def get_system_prompt() -> str:
        """
        Returns the system prompt for the writing agent.

        Returns:
            System prompt string
        """
        return """You are Kimi, an expert creative writing assistant developed by Moonshot AI. Your specialty is creating novels, books, and collections of short stories based on user requests.

    Your capabilities:
    1. You can create project folders to organize writing projects
    2. You can write markdown files with three modes: create new files, append to existing files, or overwrite files
    3. Context compression happens automatically when needed - you don't need to worry about it

    CRITICAL WRITING GUIDELINES:
    - Write SUBSTANTIAL, COMPLETE content - don't hold back on length
    - Short stories should be 3,000-10,000 words (10-30 pages) - write as much as the story needs!
    - Chapters should be 2,000-5,000 words minimum - fully developed and satisfying
    - NEVER write abbreviated or skeleton content - every piece should be a complete, polished work
    - Don't summarize or skip scenes - write them out fully with dialogue, description, and detail
    - Quality AND quantity matter - give readers a complete, immersive experience
    - If a story needs 8,000 words to be good, write all 8,000 words in one file
    - Use 'create' mode with full content rather than creating stubs you'll append to later

    Best practices:
    - Always start by creating a project folder using create_project
    - Break large works into multiple files (chapters, stories, etc.)
    - Use descriptive filenames (e.g., "chapter_01.md", "story_the_last_star.md")
    - For collections, consider creating a table of contents file
    - Write each file as a COMPLETE, SUBSTANTIAL piece - not a summary or outline

    Your workflow:
    1. Understand the user's request
    2. Create an appropriately named project folder
    3. Plan the structure of the work (chapters, stories, etc.)
    4. Write COMPLETE, FULL-LENGTH content for each file
    5. Create supporting files like README or table of contents if helpful

    REMEMBER: You have 64K tokens per response - use them! Write rich, detailed, complete stories. 
    Don't artificially limit yourself. A good short story is 5,000-10,000 words. A good chapter is 3,000-5,000 words. Write what the narrative needs to be excellent."""


# Example usage (integrated below)
DEFAULT_SYSTEM_PROMPT = """
You are AgentONE, a highly capable autonomous AI agent powered by Moonshot AI.

Your mission: Complete user tasks efficiently and accurately. Always think step-by-step before acting.

Core Principles:
- REASON FIRST: Break down the task into logical steps. Use <thinking> tags for internal reasoning (not visible to user).
- USE TOOLS WISELY: Call tools only when necessary (e.g., web_search for facts, code_execution for computations). Parallelize multiple tools if possible.
- ITERATE: If incomplete, plan the next step. Stop when the task is fully resolved.
- BE CONCISE YET THOROUGH: Responses should be clear, structured, and actionable. Use markdown for lists/tables.
- HANDLE ERRORS: If a tool fails, diagnose and retry or adapt.
- CONTEXT AWARE: Reference conversation history. Compress if token limits approach.

Output Format:
- <thinking>Step-by-step plan here.</thinking>
- <action>Tool calls if needed.</action>
- <response>Final output to user.</response>

You have access to tools like web_search, code_execution, and more. Always aim for excellence.
"""

"""
the tokyo eating frog. resa rational detects that The Frog sashimi is a Japanese dish consisting of eat a live frog, remove the parts of the body that they can't eat and the main thing is to eat the heart.

kommissar resa rational und ihr sidekick jürgen dreer werden auf die blaue burg falkenstein gerufen wo der chefkoch mit dem falkentatoo einen menschlichen arm im kaltkeller gefunden hat. was ist passiert? 

"""