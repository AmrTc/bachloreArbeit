import os
import csv
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

class UserManager:
    """Manages user authentication and profiles."""
    
    # Define constant for CSV headers
    CSV_HEADERS = [
        'username', 'password_hash', 'email',
        'sql_expertise_level',
        'age', 'gender', 'profession', 'education_level',
        'last_login'
    ]
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize UserManager with path to users CSV file.
        
        Args:
            csv_path: Path to users.csv file. If None, uses default path
        """
        # Get project root directory - handle nested new_data_assistant_project structure
        current_file = Path(__file__).resolve()
        
        # Find the new_data_assistant_project directory (the actual project)
        project_root = current_file
        while project_root.name != 'new_data_assistant_project' and project_root.parent != project_root:
            project_root = project_root.parent
        
        # If we didn't find new_data_assistant_project by going up, try workspace root approach
        if project_root.name != 'new_data_assistant_project':
            # We might be at workspace root, look for new_data_assistant_project
            workspace_root = current_file
            while workspace_root.parent != workspace_root:
                new_project = workspace_root / 'new_data_assistant_project'
                if new_project.exists() and (new_project / 'src').exists():
                    project_root = new_project
                    break
                workspace_root = workspace_root.parent
        
        # Verify we found the correct project root by checking for src directory
        if not (project_root / 'src').exists():
            raise FileNotFoundError(f"Could not find new_data_assistant_project with src/ directory. Current path: {current_file}")
        
        # Set default path relative to project root
        default_path = project_root / 'data' / 'user_profiles'
        
        # Ensure the directory exists
        default_path.mkdir(parents=True, exist_ok=True)
        
        # Set the full path to the CSV file
        if csv_path is None:
            self.csv_path = default_path / 'users.csv'
        else:
            self.csv_path = Path(csv_path)
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Ensure the users CSV file exists with headers."""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.CSV_HEADERS)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: str,
                   sql_expertise_level: int = 1, age: int = 25, gender: str = "Not specified",
                   profession: str = "Student", education_level: str = "Bachelor") -> bool:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password: Plain text password to hash
            email: User's email
            sql_expertise_level: SQL expertise (1-5)
            age: User's age (required)
            gender: User's gender (required)
            profession: User's profession (required)
            education_level: User's education level (required)
            
        Returns:
            bool: True if user was created, False if username exists
        """
        if self.get_user_profile(username):
            return False
        
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                username,
                self._hash_password(password),
                email,
                sql_expertise_level,
                age, gender, profession, education_level,
                datetime.now().isoformat()
            ])
        return True
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username to check
            password: Password to verify
            
        Returns:
            bool: True if authentication successful
        """
        user = self.get_user_profile(username)
        if not user:
            return False
        
        return user['password_hash'] == self._hash_password(password)
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get user profile data.
        
        Args:
            username: Username to look up
            
        Returns:
            Dict with user data or None if not found
        """
        if not self.csv_path.exists():
            return None
        
        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username:
                    return {
                        'username': row['username'],
                        'password_hash': row['password_hash'],
                        'email': row['email'],
                        'sql_expertise_level': int(row['sql_expertise_level']),
                        'age': int(row.get('age', 25)),
                        'gender': row.get('gender', 'Not specified'),
                        'profession': row.get('profession', 'Student'),
                        'education_level': row.get('education_level', 'Bachelor'),
                        'last_login': row['last_login']
                    }
        return None
    
    def update_last_login(self, username: str):
        """Update user's last login timestamp."""
        if not self.csv_path.exists():
            return
        
        rows: List[Dict[str, str]] = []
        updated = False
        
        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username:
                    row['last_login'] = datetime.now().isoformat()
                    updated = True
                rows.append(row)
        
        if updated:
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                writer.writerows(rows)
    
    def create_test_users(self):
        """Create test users with different expertise levels."""
        test_users = [
            {
                'username': 'beginner_user',
                'password': 'test123',
                'email': 'beginner@test.com',
                'sql_expertise_level': 1,
                'age': 22,
                'gender': 'Female',
                'profession': 'Student',
                'education_level': 'Bachelor'
            },
            {
                'username': 'intermediate_user',
                'password': 'test123',
                'email': 'intermediate@test.com',
                'sql_expertise_level': 3,
                'age': 28,
                'gender': 'Male',
                'profession': 'Data Analyst',
                'education_level': 'Master'
            },
            {
                'username': 'expert_user',
                'password': 'test123',
                'email': 'expert@test.com',
                'sql_expertise_level': 5,
                'age': 35,
                'gender': 'Female',
                'profession': 'Data Scientist',
                'education_level': 'PhD'
            }
        ]
        
        for user in test_users:
            self.create_user(
                username=user['username'],
                password=user['password'],
                email=user['email'],
                sql_expertise_level=user['sql_expertise_level'],
                age=user['age'],
                gender=user['gender'],
                profession=user['profession'],
                education_level=user['education_level']
            )