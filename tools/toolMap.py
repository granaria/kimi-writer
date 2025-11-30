


from typing import List, Dict, Any, Callable
from typing import Dict, Any, Callable

from ads.projectManager import ProjectManager
from tools import write_chapter_impl, create_project_impl, compress_context_impl






class ToolMap:

    def __init__(self):
        '''

        '''

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns the tool definitions in the format expected by kimi-k2-thinking.

        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_project",
                    "description": "Creates a new project folder in the 'output' directory with a sanitized name. This should be called first before writing any files. Only one project can be active at a time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_name": {
                                "type": "string",
                                "description": "The name for the project folder (will be sanitized for filesystem compatibility)"
                            }
                        },
                        "required": ["project_name"]
                    }
                }
            },
            
            {
                "type": "function",
                "function": {
                    "name": "write_chapter",
                    "description": "Writes content to a markdown file in the active project folder. Supports three modes: 'create' (creates new file, fails if exists), 'append' (adds content to end of existing file), 'overwrite' (replaces entire file content).",
                    "parameters": {
                        "type": "object",
                        "properties": {

                            "filename": {
                                "type": "string",
                                "description": "The name of the markdown file to write (should end in .md)"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["create", "append", "overwrite"],
                                "description": "The write mode: 'create' for new files, 'append' to add to existing, 'overwrite' to replace"
                            }
                        },
                        "required": ["filename", "content", "mode"]
                    }
                }
            },
            

            {
                "type": "function",
                "function": {
                    "name": "compress_context",
                    "description": "INTERNAL TOOL - This is automatically called by the system when token limit is approached. You should not call this manually. It compresses the conversation history to save tokens.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    
    def get_tool_map(self) -> Dict[str, Callable]:
        """
        Returns a mapping of tool names to their implementation functions.

        Returns:
            Dictionary mapping tool name strings to callable functions
        """


        return {
            "create_project": create_project_impl,
            "write_chapter": write_chapter_impl,
            "compress_context": compress_context_impl
        }
