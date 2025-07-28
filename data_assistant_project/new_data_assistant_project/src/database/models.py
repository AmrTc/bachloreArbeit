from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional, Dict, List
import json
import hashlib
import uuid

@dataclass
class User:
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    role: str  # 'admin' or 'user'
    name: Optional[str]
    profile_picture: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    sql_expertise_level: int
    domain_knowledge: int
    cognitive_load_capacity: int
    has_completed_assessment: bool = False
    google_id: Optional[str] = None  # Keep for backward compatibility

    @classmethod
    def create_user(cls, username: str, email: str, password: str, role: str = 'user', name: str = None) -> 'User':
        """Create a new User instance with hashed password."""
        return cls(
            id=None,
            username=username,
            email=email,
            password_hash=cls._hash_password(password),
            role=role,
            name=name or username,
            profile_picture=None,
            created_at=datetime.now(),
            last_login=None,
            sql_expertise_level=2,  # Default values
            domain_knowledge=2,
            cognitive_load_capacity=3,
            has_completed_assessment=False
        )
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @classmethod
    def authenticate(cls, db_path: str, username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, name, profile_picture, 
                   created_at, last_login, sql_expertise_level, domain_knowledge, 
                   cognitive_load_capacity, has_completed_assessment, google_id
            FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[3] == cls._hash_password(password):
            return cls(
                id=row[0], username=row[1], email=row[2], password_hash=row[3],
                role=row[4], name=row[5], profile_picture=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                sql_expertise_level=row[9], domain_knowledge=row[10],
                cognitive_load_capacity=row[11], has_completed_assessment=bool(row[12]),
                google_id=row[13]
            )
        return None

    @classmethod
    def get_by_id(cls, db_path: str, user_id: int) -> Optional['User']:
        """Retrieve a user by their ID."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, name, profile_picture, 
                   created_at, last_login, sql_expertise_level, domain_knowledge, 
                   cognitive_load_capacity, has_completed_assessment, google_id
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], username=row[1], email=row[2], password_hash=row[3],
                role=row[4], name=row[5], profile_picture=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                sql_expertise_level=row[9], domain_knowledge=row[10],
                cognitive_load_capacity=row[11], has_completed_assessment=bool(row[12]),
                google_id=row[13]
            )
        return None
    
    @classmethod
    def get_by_username(cls, db_path: str, username: str) -> Optional['User']:
        """Retrieve a user by their username."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, name, profile_picture, 
                   created_at, last_login, sql_expertise_level, domain_knowledge, 
                   cognitive_load_capacity, has_completed_assessment, google_id
            FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], username=row[1], email=row[2], password_hash=row[3],
                role=row[4], name=row[5], profile_picture=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                sql_expertise_level=row[9], domain_knowledge=row[10],
                cognitive_load_capacity=row[11], has_completed_assessment=bool(row[12]),
                google_id=row[13]
            )
        return None

    def save(self, db_path: str):
        """Save or update user in database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.id is None:
            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, name, profile_picture, 
                                 created_at, last_login, sql_expertise_level, domain_knowledge, 
                                 cognitive_load_capacity, has_completed_assessment, google_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.username, self.email, self.password_hash, self.role, self.name, 
                self.profile_picture, self.created_at.isoformat(), 
                self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.domain_knowledge, self.cognitive_load_capacity,
                self.has_completed_assessment, self.google_id
            ))
            self.id = cursor.lastrowid
        else:
            # Update existing user
            cursor.execute("""
                UPDATE users
                SET username = ?, email = ?, password_hash = ?, role = ?, name = ?, 
                    profile_picture = ?, last_login = ?, sql_expertise_level = ?, 
                    domain_knowledge = ?, cognitive_load_capacity = ?, has_completed_assessment = ?
                WHERE id = ?
            """, (
                self.username, self.email, self.password_hash, self.role, self.name,
                self.profile_picture, self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.domain_knowledge, self.cognitive_load_capacity,
                self.has_completed_assessment, self.id
            ))
        
        conn.commit()
        conn.close()

    def update_login(self, db_path: str):
        """Update user's last login time."""
        self.last_login = datetime.now()
        self.save(db_path)
    
    def complete_assessment(self, db_path: str, sql_level: int, domain_level: int):
        """Mark assessment as completed and update levels."""
        self.has_completed_assessment = True
        self.sql_expertise_level = sql_level
        self.domain_knowledge = domain_level
        self.cognitive_load_capacity = max(1, min(3, sql_level - 1))  # Map to cognitive capacity
        self.save(db_path)


@dataclass
class ChatSession:
    id: Optional[int]
    user_id: int
    session_uuid: str
    user_message: str
    system_response: str
    sql_query: Optional[str]
    explanation_given: bool
    created_at: datetime
    
    @classmethod
    def create_session(cls, user_id: int, user_message: str, system_response: str, 
                      sql_query: str = None, explanation_given: bool = False) -> 'ChatSession':
        """Create a new chat session."""
        return cls(
            id=None,
            user_id=user_id,
            session_uuid=str(uuid.uuid4()),
            user_message=user_message,
            system_response=system_response,
            sql_query=sql_query,
            explanation_given=explanation_given,
            created_at=datetime.now()
        )
    
    def save(self, db_path: str):
        """Save chat session to database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_sessions (user_id, session_uuid, user_message, system_response, 
                                     sql_query, explanation_given, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.user_id, self.session_uuid, self.user_message, self.system_response,
            self.sql_query, self.explanation_given, self.created_at.isoformat()
        ))
        self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    @classmethod
    def get_user_sessions(cls, db_path: str, user_id: int, limit: int = 50) -> List['ChatSession']:
        """Get recent chat sessions for a user."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, session_uuid, user_message, system_response, 
                   sql_query, explanation_given, created_at
            FROM chat_sessions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append(cls(
                id=row[0], user_id=row[1], session_uuid=row[2], user_message=row[3],
                system_response=row[4], sql_query=row[5], explanation_given=bool(row[6]),
                created_at=datetime.fromisoformat(row[7])
            ))
        
        return sessions


@dataclass
class ExplanationFeedback:
    id: Optional[int]
    user_id: int
    session_id: int
    explanation_given: bool
    was_needed: Optional[bool]
    was_helpful: Optional[bool]
    would_have_been_needed: Optional[bool]
    created_at: datetime
    
    @classmethod
    def create_feedback(cls, user_id: int, session_id: int, explanation_given: bool,
                       was_needed: bool = None, was_helpful: bool = None, 
                       would_have_been_needed: bool = None) -> 'ExplanationFeedback':
        """Create new explanation feedback."""
        return cls(
            id=None,
            user_id=user_id,
            session_id=session_id,
            explanation_given=explanation_given,
            was_needed=was_needed,
            was_helpful=was_helpful,
            would_have_been_needed=would_have_been_needed,
            created_at=datetime.now()
        )
    
    def save(self, db_path: str):
        """Save feedback to database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO explanation_feedback (user_id, session_id, explanation_given, 
                                            was_needed, was_helpful, would_have_been_needed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.user_id, self.session_id, self.explanation_given,
            self.was_needed, self.was_helpful, self.would_have_been_needed,
            self.created_at.isoformat()
        ))
        self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    @classmethod
    def get_all_feedback(cls, db_path: str) -> List['ExplanationFeedback']:
        """Get all feedback for admin dashboard."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ef.id, ef.user_id, ef.session_id, ef.explanation_given, 
                   ef.was_needed, ef.was_helpful, ef.would_have_been_needed, ef.created_at,
                   u.username, cs.user_message
            FROM explanation_feedback ef
            JOIN users u ON ef.user_id = u.id
            JOIN chat_sessions cs ON ef.session_id = cs.id
            ORDER BY ef.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback = cls(
                id=row[0], user_id=row[1], session_id=row[2], explanation_given=bool(row[3]),
                was_needed=bool(row[4]) if row[4] is not None else None,
                was_helpful=bool(row[5]) if row[5] is not None else None,
                would_have_been_needed=bool(row[6]) if row[6] is not None else None,
                created_at=datetime.fromisoformat(row[7])
            )
            # Add extra info for admin dashboard
            feedback.username = row[8]
            feedback.user_message = row[9]
            feedback_list.append(feedback)
        
        return feedback_list 