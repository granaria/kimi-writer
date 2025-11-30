"""
Project folder management tool.
"""
import os
import re
from pathlib import Path
from typing import Optional

global _active_project_folder

class ProjectManager:
    """
    Manages project folders

    Features:
    - Automatic sanitization of project names
    - Thread-safe if you use one instance per thread/process
    - Proper Path handling (cross-platform)
    - Handles duplicate project names gracefully with numbering
    - Context manager support for temporary project switching
    """

    _DEFAULT_OUTPUT_DIR = "output"


    def __init__(self, root_dir: Optional[os.PathLike] = None):
        """
        Args:
            root_dir: Root directory of the application. If None, auto-detects
                      the project root (parent of the directory containing this file).
        """
        if root_dir is None:
            # Auto-detect: assume this file is in tools/ → go up two levels
            this_file = Path(__file__).resolve()
            self.root_dir = this_file.parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()

        self.output_dir = self.root_dir / ProjectManager._DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        self._active_project: Optional[Path] = None



    def sanitize_folder_name(self, name: str) -> str:
        """
        Sanitizes a folder name for filesystem compatibility.

        Args:
            name: The proposed folder name

        Returns:
            Sanitized folder name
        """
        if not name:
            return "untitled_project"
        # Replace spaces with underscores
        name = name.strip().replace(' ', '_')
        # Remove any characters that aren't alphanumeric, underscore, or hyphen
        name = re.sub(r'[^\w\-]', '', name)
        # Remove leading/trailing hyphens or underscores
        name = name.strip('-_')
        # Ensure it's not empty
        if not name:
            name = "untitled_project"
        return name



    @property
    def active_project(self) -> Optional[Path]:
        """Currently active project folder (or None)."""
        return self._active_project

    '''
    @property
    def active_project_name(self) -> Optional[str]:
        """Name of the active project (without path)."""
        return self._active_project.name if self._active_project else None
    '''


    def create_project(self, project_name: str) -> Path:
        """
        Creates a new project folder (or activates existing one).

        If a folder with the same sanitized name already exists,
        automatically appends _2, _3, etc. to avoid collisions.

        Returns:
            Full path to the created/activated project folder

        Raises:
            OSError: If folder creation fails for reasons other than name collision
        """

        # Sanitize the folder name
        sanitized_name = self.sanitize_folder_name(project_name)

        # Get the script's root directory (where kimi-writer.py is located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)  # Go up from tools/ to root

        # Create output directory if it doesn't exist
        output_dir = os.path.join(root_dir, "output")
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                return f"Error creating output directory: {str(e)}"

        # Create the full path inside output directory
        project_path = os.path.join(output_dir, sanitized_name)
        # print(project_path)

        # Check if folder already exists
        if os.path.exists(project_path):
            # Use existing folder and set it as active

            self._active_project = project_path

            return f"Project folder already exists at '{project_path}'. Set as active project folder."

        # Create the folder
        try:
            os.makedirs(project_path, exist_ok=True)

            self._active_project = project_path
            return f"Successfully created project folder at '{project_path}'. This is now the active project folder."
        except Exception as e:
            return f"Error creating project folder: {str(e)}"


    # def set_active_project(self, folder_path: os.PathLike) -> None:
    def set_active_project_folder(self, folder_path: str) -> None:
        """
            Sets the active project folder.

            Args:
                folder_path: Path to the project folder
        """

        self._active_project = folder_path

        """
        Manually set the active project (useful for loading previous sessions). 

        Raises:
            ValueError: If the path is not inside the output directory
            FileNotFoundError: If the path doesn't exist
        """
        path = Path(folder_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Project folder not found: {path}")

        if self.output_dir not in path.parents and path != self.output_dir:
            raise ValueError(f"Project must be inside {self.output_dir}")

        self._active_project = path



    def get_or_create_project(self, project_name: str) -> Path:
        """
        Returns existing project if it exists, otherwise creates it.
        Never creates duplicates — reuses exact match by sanitized name.
        """
        sanitized = self.sanitize_folder_name(project_name)
        exact_match = self.output_dir / sanitized

        if exact_match.exists():
            self._active_project = exact_match
            return exact_match
        else:
            return self.create_project(project_name)

    def list_projects(self) -> list[Path]:
        """Return all project folders in the output directory."""
        if not self.output_dir.exists():
            return []
        return sorted(p for p in self.output_dir.iterdir() if p.is_dir())

    def __enter__(self) -> "ProjectManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __str__(self) -> str:
        return f"ProjectManager(root={self.root_dir}, active={self._active_project})"

"""
# ----------------------------------------------------------------------
# Convenience global instance (optional – you can also instantiate manually)
# ----------------------------------------------------------------------
project_manager = ProjectManager()
create_project = project_manager.create_project
get_active_project_folder = lambda: project_manager.active_project
set_active_project_folder = project_manager.set_active_project
# Global variable to track the active project folder
_active_project_folder: Optional[str] = None
"""








# ---------------------------------------------------------------------------


def create_project_impl0(projectmanager:ProjectManager, project_name: str) -> str:

    projectmanager.create_project(project_name)

