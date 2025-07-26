import os
from pathlib import Path
from .path_utils import get_project_root, get_absolute_path, get_relative_path

class DataPathUtils:
    """Utility class for managing data directory paths."""
    
    def __init__(self):
        self.project_root = get_project_root()
        # Update data root to be directly in project root
        self.data_root = self.project_root
        
        # Define standard data subdirectories
        self.user_profiles_dir = self.data_root / 'user_profiles'
        self.datasets_dir = self.data_root / 'datasets'
        self.evaluation_data_dir = self.data_root / 'evaluation_data'
        
        # Ensure directories exist
        self.ensure_data_directories()
    
    def ensure_data_directories(self):
        """Ensure all standard data directories exist."""
        directories = [
            self.data_root,
            self.user_profiles_dir,
            self.datasets_dir,
            self.evaluation_data_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_user_profiles_path(self, filename: str = 'users.csv') -> Path:
        """Get absolute path to a file in the user_profiles directory."""
        return self.user_profiles_dir / filename
    
    def get_dataset_path(self, filename: str) -> Path:
        """Get absolute path to a dataset file."""
        return self.datasets_dir / filename
    
    def get_evaluation_data_path(self, filename: str) -> Path:
        """Get absolute path to an evaluation data file."""
        return self.evaluation_data_dir / filename
    
    def get_relative_data_path(self, absolute_path: str | Path) -> str:
        """Convert absolute path to path relative to data directory."""
        try:
            path = Path(absolute_path) if isinstance(absolute_path, str) else absolute_path
            return str(path.relative_to(self.data_root))
        except ValueError:
            return str(absolute_path)
    
    def get_absolute_data_path(self, relative_path: str | Path) -> Path:
        """Convert path relative to data directory into absolute path."""
        return self.data_root / str(relative_path)
    
    def list_datasets(self) -> list[str]:
        """List all files in the datasets directory."""
        return [f.name for f in self.datasets_dir.glob('*') if f.is_file()]
    
    def list_user_profiles(self) -> list[str]:
        """List all files in the user_profiles directory."""
        return [f.name for f in self.user_profiles_dir.glob('*') if f.is_file()]
    
    def list_evaluation_data(self) -> list[str]:
        """List all files in the evaluation_data directory."""
        return [f.name for f in self.evaluation_data_dir.glob('*') if f.is_file()] 