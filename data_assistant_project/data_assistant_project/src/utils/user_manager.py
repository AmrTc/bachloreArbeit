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
        'sql_expertise_level', 'domain_knowledge',
        'last_login'
    ]
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize UserManager with path to users CSV file.
        
        Args:
            csv_path: Path to users.csv file. If None, uses default path
        """
        # Get project root directory
        current_file = Path(__file__).resolve()
        while current_file.name != 'data_assistant_project' and current_file.parent != current_file:
            current_file = current_file.parent
        project_root = current_file
        
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
                   sql_expertise_level: int = 1, domain_knowledge: int = 1) -> bool:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password: Plain text password to hash
            email: User's email
            sql_expertise_level: SQL expertise (1-5)
            domain_knowledge: Domain knowledge (1-5)
            
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
                domain_knowledge,
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
                        'domain_knowledge': int(row['domain_knowledge']),
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
                'domain_knowledge': 1
            },
            {
                'username': 'intermediate_user',
                'password': 'test123',
                'email': 'intermediate@test.com',
                'sql_expertise_level': 3,
                'domain_knowledge': 3
            },
            {
                'username': 'expert_user',
                'password': 'test123',
                'email': 'expert@test.com',
                'sql_expertise_level': 5,
                'domain_knowledge': 5
            }
        ]
        
        for user in test_users:
            self.create_user(
                username=user['username'],
                password=user['password'],
                email=user['email'],
                sql_expertise_level=user['sql_expertise_level'],
                domain_knowledge=user['domain_knowledge']
            )