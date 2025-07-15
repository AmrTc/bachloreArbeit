from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional, Dict
import json

@dataclass
class User:
    id: Optional[int]
    google_id: str
    email: str
    name: str
    profile_picture: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    sql_expertise_level: int
    domain_knowledge: int
    cognitive_load_capacity: int

    @classmethod
    def from_google_data(cls, google_data: Dict) -> 'User':
        """Create a User instance from Google OAuth data."""
        return cls(
            id=None,
            google_id=google_data['sub'],
            email=google_data['email'],
            name=google_data.get('name', ''),
            profile_picture=google_data.get('picture'),
            created_at=datetime.now(),
            last_login=None,
            sql_expertise_level=2,  # Default values
            domain_knowledge=2,
            cognitive_load_capacity=3
        )

    @classmethod
    def get_by_google_id(cls, db_path: str, google_id: str) -> Optional['User']:
        """Retrieve a user by their Google ID."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, google_id, email, name, profile_picture, created_at, 
                   last_login, sql_expertise_level, domain_knowledge, cognitive_load_capacity
            FROM users WHERE google_id = ?
        """, (google_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0],
                google_id=row[1],
                email=row[2],
                name=row[3],
                profile_picture=row[4],
                created_at=datetime.fromisoformat(row[5]),
                last_login=datetime.fromisoformat(row[6]) if row[6] else None,
                sql_expertise_level=row[7],
                domain_knowledge=row[8],
                cognitive_load_capacity=row[9]
            )
        return None

    def save(self, db_path: str):
        """Save or update user in database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.id is None:
            # Insert new user
            cursor.execute("""
                INSERT INTO users (google_id, email, name, profile_picture, created_at,
                                 last_login, sql_expertise_level, domain_knowledge, cognitive_load_capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.google_id, self.email, self.name, self.profile_picture,
                self.created_at.isoformat(), self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.domain_knowledge, self.cognitive_load_capacity
            ))
            self.id = cursor.lastrowid
        else:
            # Update existing user
            cursor.execute("""
                UPDATE users
                SET email = ?, name = ?, profile_picture = ?, last_login = ?,
                    sql_expertise_level = ?, domain_knowledge = ?, cognitive_load_capacity = ?
                WHERE id = ?
            """, (
                self.email, self.name, self.profile_picture,
                self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.domain_knowledge, self.cognitive_load_capacity,
                self.id
            ))
        
        conn.commit()
        conn.close()

    def update_login(self, db_path: str):
        """Update user's last login time."""
        self.last_login = datetime.now()
        self.save(db_path) 