import os
from pathlib import Path
from .path_utils import get_project_root, get_absolute_path, get_relative_path

class SrcPathUtils:
    """Utility class for managing src directory paths and imports."""
    
    def __init__(self):
        self.project_root = get_project_root()
        # Set src root directory
        self.src_root = self.project_root / 'src'
        
        # Define standard src subdirectories
        self.agents_dir = self.src_root / 'agents'
        self.utils_dir = self.src_root / 'utils'
        self.database_dir = self.src_root / 'database'
        
        # Ensure directories exist
        self.ensure_src_directories()
    
    def ensure_src_directories(self):
        """Ensure all standard src directories exist."""
        directories = [
            self.src_root,
            self.agents_dir,
            self.utils_dir,
            self.database_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_agent_path(self, filename: str) -> Path:
        """Get absolute path to a file in the agents directory."""
        return self.agents_dir / filename
    
    def get_utils_path(self, filename: str) -> Path:
        """Get absolute path to a file in the utils directory."""
        return self.utils_dir / filename
    
    def get_database_path(self, filename: str) -> Path:
        """Get absolute path to a file in the database directory."""
        return self.database_dir / filename
    
    def get_relative_src_path(self, absolute_path: str | Path) -> str:
        """Convert absolute path to path relative to src directory."""
        try:
            path = Path(absolute_path) if isinstance(absolute_path, str) else absolute_path
            return str(path.relative_to(self.src_root))
        except ValueError:
            return str(absolute_path)
    
    def get_absolute_src_path(self, relative_path: str | Path) -> Path:
        """Convert path relative to src directory into absolute path."""
        return self.src_root / str(relative_path)
    
    def get_import_path(self, module_path: str) -> str:
        """
        Get the proper import path for a module.
        
        Args:
            module_path: Path relative to src directory (e.g. 'utils/my_config.py')
            
        Returns:
            Import path (e.g. 'src.utils.my_config')
        """
        # Remove .py extension if present
        module_path = str(module_path)
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
            
        # Convert path separators to dots and prepend src
        return 'src.' + module_path.replace('/', '.')
    
    def list_agents(self) -> list[str]:
        """List all Python files in the agents directory."""
        return [f.name for f in self.agents_dir.glob('*.py') if f.is_file()]
    
    def list_utils(self) -> list[str]:
        """List all Python files in the utils directory."""
        return [f.name for f in self.utils_dir.glob('*.py') if f.is_file()]
    
    def list_database_files(self) -> list[str]:
        """List all files in the database directory."""
        return [f.name for f in self.database_dir.glob('*') if f.is_file()]
    
    @staticmethod
    def get_instance():
        """Get or create singleton instance of SrcPathUtils."""
        if not hasattr(SrcPathUtils, '_instance'):
            SrcPathUtils._instance = SrcPathUtils()
        return SrcPathUtils._instance 