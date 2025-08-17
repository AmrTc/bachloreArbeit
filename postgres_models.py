from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List, Any
import json
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    role: str  # 'admin' or 'user'
    created_at: datetime
    last_login: Optional[datetime]
    sql_expertise_level: int
    cognitive_load_capacity: int
    has_completed_assessment: bool = False
    
    # CLT-CFT Assessment Fields
    sql_expertise: int = 0
    data_analysis_fundamentals: int = 0
    business_analytics: int = 0
    forecasting_statistics: int = 0
    data_visualization: int = 0
    domain_knowledge_retail: int = 0
    total_assessment_score: int = 0
    user_level_category: str = "Beginner"
    
    # CLT-CFT Agent Profile Fields (for compatibility with UserProfile)
    sql_concept_levels: Dict[str, int] = None  # Will be initialized as empty dict
    prior_query_history: List[Dict] = None  # Will be initialized as empty list
    learning_preferences: Dict[str, Any] = None  # Will be initialized as empty dict
    
    # User Demographics and Background Information
    age: Optional[int] = None
    gender: Optional[str] = None
    profession: Optional[str] = None
    education_level: Optional[str] = None
    study_training: Optional[str] = None

    def __post_init__(self):
        """Initialize default values for complex fields."""
        if self.sql_concept_levels is None:
            self.sql_concept_levels = {}
        if self.prior_query_history is None:
            self.prior_query_history = []
        if self.learning_preferences is None:
            self.learning_preferences = {}

    @classmethod
    def create_user(cls, username: str, password: str, role: str = 'user') -> 'User':
        """Create a new User instance with hashed password."""
        return cls(
            id=None,
            username=username,
            password_hash=cls._hash_password(password),
            role=role,
            created_at=datetime.now(),
            last_login=None,
            sql_expertise_level=2,  # Default values
            cognitive_load_capacity=3,
            has_completed_assessment=False,
            sql_expertise=2,  # Default SQL expertise level
            sql_concept_levels={},
            prior_query_history=[],
            learning_preferences={},
            age=None,
            gender=None,
            profession=None,
            education_level=None,
            study_training=None
        )
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @classmethod
    def authenticate(cls, db_config: Dict[str, Any], username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password using PostgreSQL."""
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, password_hash, role,
                       created_at, last_login, sql_expertise_level, 
                       cognitive_load_capacity, has_completed_assessment,
                       sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                       data_visualization, domain_knowledge_retail, total_assessment_score,
                       user_level_category, age, gender, profession, education_level, study_training
                FROM users WHERE username = %s
            """, (username,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row and row[2] == cls._hash_password(password):
                return cls(
                    id=row[0], username=row[1], password_hash=row[2],
                    role=row[3],
                    created_at=row[4] if isinstance(row[4], datetime) else datetime.fromisoformat(str(row[4])),
                    last_login=row[5] if row[5] and isinstance(row[5], datetime) else 
                               (datetime.fromisoformat(str(row[5])) if row[5] else None),
                    sql_expertise_level=row[6] or 2, 
                    cognitive_load_capacity=row[7] or 3, 
                    has_completed_assessment=bool(row[8]) if row[8] is not None else False,
                    sql_expertise=row[9] if row[9] is not None else 0,
                    data_analysis_fundamentals=row[10] if row[10] is not None else 0,
                    business_analytics=row[11] if row[11] is not None else 0,
                    forecasting_statistics=row[12] if row[12] is not None else 0,
                    data_visualization=row[13] if row[13] is not None else 0,
                    domain_knowledge_retail=row[14] if row[14] is not None else 0,
                    total_assessment_score=row[15] if row[15] is not None else 0,
                    user_level_category=row[16] if row[16] else "Beginner",
                    age=row[17],
                    gender=row[18],
                    profession=row[19],
                    education_level=row[20],
                    study_training=row[21]
                )
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def save(self, db_config: Dict[str, Any]):
        """Save user to PostgreSQL database."""
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            if self.id is None:
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (
                        username, password_hash, role, created_at, last_login,
                        sql_expertise_level, cognitive_load_capacity, has_completed_assessment,
                        sql_expertise, data_analysis_fundamentals, business_analytics,
                        forecasting_statistics, data_visualization, domain_knowledge_retail,
                        total_assessment_score, user_level_category, age, gender,
                        profession, education_level, study_training
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    self.username, self.password_hash, self.role, self.created_at, self.last_login,
                    self.sql_expertise_level, self.cognitive_load_capacity, self.has_completed_assessment,
                    self.sql_expertise, self.data_analysis_fundamentals, self.business_analytics,
                    self.forecasting_statistics, self.data_visualization, self.domain_knowledge_retail,
                    self.total_assessment_score, self.user_level_category, self.age, self.gender,
                    self.profession, self.education_level, self.study_training
                ))
                
                self.id = cursor.fetchone()[0]
            else:
                # Update existing user
                cursor.execute("""
                    UPDATE users SET
                        username = %s, password_hash = %s, role = %s, created_at = %s, last_login = %s,
                        sql_expertise_level = %s, cognitive_load_capacity = %s, has_completed_assessment = %s,
                        sql_expertise = %s, data_analysis_fundamentals = %s, business_analytics = %s,
                        forecasting_statistics = %s, data_visualization = %s, domain_knowledge_retail = %s,
                        total_assessment_score = %s, user_level_category = %s, age = %s, gender = %s,
                        profession = %s, education_level = %s, study_training = %s
                    WHERE id = %s
                """, (
                    self.username, self.password_hash, self.role, self.created_at, self.last_login,
                    self.sql_expertise_level, self.cognitive_load_capacity, self.has_completed_assessment,
                    self.sql_expertise, self.data_analysis_fundamentals, self.business_analytics,
                    self.forecasting_statistics, self.data_visualization, self.domain_knowledge_retail,
                    self.total_assessment_score, self.user_level_category, self.age, self.gender,
                    self.profession, self.education_level, self.study_training, self.id
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise

    def update_login(self, db_config: Dict[str, Any]):
        """Update last login timestamp."""
        try:
            self.last_login = datetime.now()
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_login = %s WHERE id = %s
            """, (self.last_login, self.id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating login: {e}")
            raise

    def complete_assessment(self, db_config: Dict[str, Any], sql_level: int):
        """Complete user assessment and update expertise levels."""
        try:
            self.sql_expertise_level = sql_level
            self.has_completed_assessment = True
            
            # Update assessment fields based on SQL level
            if sql_level >= 4:
                self.sql_expertise = 4
                self.data_analysis_fundamentals = 4
                self.business_analytics = 3
                self.forecasting_statistics = 3
                self.data_visualization = 4
                self.domain_knowledge_retail = 3
                self.user_level_category = "Advanced"
            elif sql_level >= 3:
                self.sql_expertise = 3
                self.data_analysis_fundamentals = 3
                self.business_analytics = 2
                self.forecasting_statistics = 2
                self.data_visualization = 3
                self.domain_knowledge_retail = 2
                self.user_level_category = "Intermediate"
            else:
                self.sql_expertise = sql_level
                self.data_analysis_fundamentals = sql_level
                self.business_analytics = max(1, sql_level - 1)
                self.forecasting_statistics = max(1, sql_level - 1)
                self.data_visualization = sql_level
                self.domain_knowledge_retail = max(1, sql_level - 1)
                self.user_level_category = "Beginner"
            
            # Calculate total score
            self.total_assessment_score = (
                self.sql_expertise + self.data_analysis_fundamentals + 
                self.business_analytics + self.forecasting_statistics + 
                self.data_visualization + self.domain_knowledge_retail
            )
            
            # Save to database
            self.save(db_config)
            
        except Exception as e:
            logger.error(f"Error completing assessment: {e}")
            raise
