from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional, Dict, List, Any
import json
import hashlib
import uuid

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
    def authenticate(cls, db_path: str, username: str, password: str) -> Optional['User']:
        """Authenticate user with username and password."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, password_hash, role,
                   created_at, last_login, sql_expertise_level, 
                   cognitive_load_capacity, has_completed_assessment,
                   sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                   data_visualization, domain_knowledge_retail, total_assessment_score,
                   user_level_category, age, gender, profession, education_level, study_training
            FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[2] == cls._hash_password(password):
            return cls(
                id=row[0], username=row[1], password_hash=row[2],
                role=row[3],
                created_at=datetime.fromisoformat(row[4]),
                last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                sql_expertise_level=row[6], 
                cognitive_load_capacity=row[7], has_completed_assessment=bool(row[8]),
                data_analysis_fundamentals=row[9] if len(row) > 9 else 0,
                business_analytics=row[10] if len(row) > 10 else 0,
                forecasting_statistics=row[11] if len(row) > 11 else 0,
                data_visualization=row[12] if len(row) > 12 else 0,
                domain_knowledge_retail=row[13] if len(row) > 13 else 0,
                total_assessment_score=row[14] if len(row) > 14 else 0,
                user_level_category=row[15] if len(row) > 15 else "Beginner",
                sql_concept_levels={},
                prior_query_history=[],
                learning_preferences={},
                age=row[16] if len(row) > 16 else None,
                gender=row[17] if len(row) > 17 else None,
                profession=row[18] if len(row) > 18 else None,
                education_level=row[19] if len(row) > 19 else None,
                study_training=row[20] if len(row) > 20 else None
            )
        return None

    @classmethod
    def get_by_id(cls, db_path: str, user_id: int) -> Optional['User']:
        """Retrieve a user by their ID."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, password_hash, role,
                   created_at, last_login, sql_expertise_level, 
                   cognitive_load_capacity, has_completed_assessment,
                   sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                   data_visualization, domain_knowledge_retail, total_assessment_score,
                   user_level_category, age, gender, profession, education_level, study_training
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], username=row[1], password_hash=row[2],
                role=row[3],
                created_at=datetime.fromisoformat(row[4]),
                last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                sql_expertise_level=row[6], 
                cognitive_load_capacity=row[7], has_completed_assessment=bool(row[8]),
                data_analysis_fundamentals=row[9] if len(row) > 9 else 0,
                business_analytics=row[10] if len(row) > 10 else 0,
                forecasting_statistics=row[11] if len(row) > 11 else 0,
                data_visualization=row[12] if len(row) > 12 else 0,
                domain_knowledge_retail=row[13] if len(row) > 13 else 0,
                total_assessment_score=row[14] if len(row) > 14 else 0,
                user_level_category=row[15] if len(row) > 15 else "Beginner",
                sql_concept_levels={},
                prior_query_history=[],
                learning_preferences={},
                age=row[16] if len(row) > 16 else None,
                gender=row[17] if len(row) > 17 else None,
                profession=row[18] if len(row) > 18 else None,
                education_level=row[19] if len(row) > 19 else None,
                study_training=row[20] if len(row) > 20 else None
            )
        return None
    
    @classmethod
    def get_by_username(cls, db_path: str, username: str) -> Optional['User']:
        """Retrieve a user by their username."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, password_hash, role,
                   created_at, last_login, sql_expertise_level, 
                   cognitive_load_capacity, has_completed_assessment,
                   sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                   data_visualization, domain_knowledge_retail, total_assessment_score,
                   user_level_category, age, gender, profession, education_level, study_training
            FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], username=row[1], password_hash=row[2],
                role=row[3],
                created_at=datetime.fromisoformat(row[4]),
                last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                sql_expertise_level=row[6], 
                cognitive_load_capacity=row[7], has_completed_assessment=bool(row[8]),
                data_analysis_fundamentals=row[9] if len(row) > 9 else 0,
                business_analytics=row[10] if len(row) > 10 else 0,
                forecasting_statistics=row[11] if len(row) > 11 else 0,
                data_visualization=row[12] if len(row) > 12 else 0,
                domain_knowledge_retail=row[13] if len(row) > 13 else 0,
                total_assessment_score=row[14] if len(row) > 14 else 0,
                user_level_category=row[15] if len(row) > 15 else "Beginner",
                sql_concept_levels={},
                prior_query_history=[],
                learning_preferences={},
                age=row[16] if len(row) > 16 else None,
                gender=row[17] if len(row) > 17 else None,
                profession=row[18] if len(row) > 18 else None,
                education_level=row[19] if len(row) > 19 else None,
                study_training=row[20] if len(row) > 20 else None
            )
        return None

    def save(self, db_path: str):
        """Save or update user in database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.id is None:
            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, password_hash, role,
                                 created_at, last_login, sql_expertise_level, 
                                 cognitive_load_capacity, has_completed_assessment,
                                 sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                                 data_visualization, domain_knowledge_retail, total_assessment_score,
                                 user_level_category, age, gender, profession, education_level, study_training)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.username, self.password_hash, self.role, 
                self.created_at.isoformat(), 
                self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.cognitive_load_capacity,
                self.has_completed_assessment,
                self.sql_expertise, self.data_analysis_fundamentals, self.business_analytics, self.forecasting_statistics,
                self.data_visualization, self.domain_knowledge_retail, self.total_assessment_score,
                self.user_level_category, self.age, self.gender, self.profession, self.education_level, self.study_training
            ))
            self.id = cursor.lastrowid
        else:
            # Update existing user
            cursor.execute("""
                UPDATE users
                SET username = ?, password_hash = ?, role = ?, 
                    last_login = ?, sql_expertise_level = ?, 
                    cognitive_load_capacity = ?, has_completed_assessment = ?,
                    sql_expertise = ?, data_analysis_fundamentals = ?, business_analytics = ?, forecasting_statistics = ?,
                    data_visualization = ?, domain_knowledge_retail = ?, total_assessment_score = ?,
                    user_level_category = ?, age = ?, gender = ?, profession = ?, education_level = ?, study_training = ?
                WHERE id = ?
            """, (
                self.username, self.password_hash, self.role,
                self.last_login.isoformat() if self.last_login else None,
                self.sql_expertise_level, self.cognitive_load_capacity,
                self.has_completed_assessment,
                self.sql_expertise, self.data_analysis_fundamentals, self.business_analytics, self.forecasting_statistics,
                self.data_visualization, self.domain_knowledge_retail, self.total_assessment_score,
                self.user_level_category, self.age, self.gender, self.profession, self.education_level, self.study_training, self.id
            ))
        
        conn.commit()
        conn.close()

    def update_login(self, db_path: str):
        """Update user's last login time."""
        self.last_login = datetime.now()
        self.save(db_path)
    
    def complete_assessment(self, db_path: str, sql_level: int):
        """Mark assessment as completed and update levels."""
        self.has_completed_assessment = True
        self.sql_expertise_level = sql_level
        self.cognitive_load_capacity = max(1, min(3, sql_level - 1))  # Map to cognitive capacity
        self.save(db_path)
    
    def complete_comprehensive_assessment(self, db_path: str, domain_scores: Dict[str, int]):
        """Complete comprehensive 6-domain assessment and update user profile."""
        # Update domain scores
        self.sql_expertise = domain_scores.get('sql_expertise', 0)
        self.data_analysis_fundamentals = domain_scores.get('data_analysis_fundamentals', 0)
        self.business_analytics = domain_scores.get('business_analytics', 0)
        self.forecasting_statistics = domain_scores.get('forecasting_statistics', 0)
        self.data_visualization = domain_scores.get('data_visualization', 0)
        self.domain_knowledge_retail = domain_scores.get('domain_knowledge_retail', 0)
        
        # Calculate total score
        self.total_assessment_score = sum([
            self.sql_expertise,
            self.data_analysis_fundamentals,
            self.business_analytics,
            self.forecasting_statistics,
            self.data_visualization,
            self.domain_knowledge_retail
        ])
        
        # Determine user level category
        if self.total_assessment_score <= 5:
            self.user_level_category = "Beginner"
        elif self.total_assessment_score <= 10:
            self.user_level_category = "Novice"
        elif self.total_assessment_score <= 15:
            self.user_level_category = "Intermediate"
        elif self.total_assessment_score <= 20:
            self.user_level_category = "Advanced"
        else:
            self.user_level_category = "Expert"
        
        # Mark assessment as completed
        self.has_completed_assessment = True
        
        # Update legacy fields for backward compatibility
        self.sql_expertise_level = max(1, min(5, self.total_assessment_score // 4))
        self.cognitive_load_capacity = max(1, min(3, self.total_assessment_score // 7))
        
        # Save to database
        self.save(db_path)

    def update_user_demographics(self, db_path: str, age: int = None, gender: str = None, profession: str = None, 
                                education_level: str = None, study_training: str = None):
        """Update user demographic information."""
        if age is not None:
            self.age = age
        if gender is not None:
            self.gender = gender
        if profession is not None:
            self.profession = profession
        if education_level is not None:
            self.education_level = education_level
        if study_training is not None:
            self.study_training = study_training
        
        self.save(db_path)

    @classmethod
    def get_all_users(cls, db_path: str) -> List['User']:
        """Get all users for admin dashboard."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, password_hash, role,
                   created_at, last_login, sql_expertise_level, 
                   cognitive_load_capacity, has_completed_assessment,
                   sql_expertise, data_analysis_fundamentals, business_analytics, forecasting_statistics,
                   data_visualization, domain_knowledge_retail, total_assessment_score,
                   user_level_category, age, gender, profession, education_level, study_training
            FROM users
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append(cls(
                id=row[0], username=row[1], password_hash=row[2],
                role=row[3],
                created_at=datetime.fromisoformat(row[4]),
                last_login=datetime.fromisoformat(row[5]) if row[5] else None,
                sql_expertise_level=row[6], 
                cognitive_load_capacity=row[7], has_completed_assessment=bool(row[8]),
                sql_expertise=row[9] if len(row) > 9 else 0,
                data_analysis_fundamentals=row[10] if len(row) > 10 else 0,
                business_analytics=row[11] if len(row) > 11 else 0,
                forecasting_statistics=row[12] if len(row) > 12 else 0,
                data_visualization=row[13] if len(row) > 13 else 0,
                domain_knowledge_retail=row[14] if len(row) > 14 else 0,
                total_assessment_score=row[15] if len(row) > 15 else 0,
                user_level_category=row[16] if len(row) > 16 else "Beginner",
                sql_concept_levels={},
                prior_query_history=[],
                learning_preferences={},
                age=row[17] if len(row) > 17 else None,
                gender=row[18] if len(row) > 18 else None,
                profession=row[19] if len(row) > 19 else None,
                education_level=row[20] if len(row) > 20 else None,
                study_training=row[21] if len(row) > 21 else None
            ))
        
        return users


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
    
    @classmethod
    def delete_user_sessions(cls, db_path: str, user_id: int):
        """Delete all chat sessions for a specific user."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


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


@dataclass
class ComprehensiveFeedback:
    id: Optional[int]
    user_id: int
    frequency_rating: int
    frequency_reason: Optional[str]
    explanation_quality_rating: int
    explanation_quality_reason: Optional[str]
    system_helpfulness_rating: int
    system_helpfulness_reason: Optional[str]
    learning_improvement_rating: int
    learning_improvement_reason: Optional[str]
    auto_explanation: bool
    auto_reason: Optional[str]
    system_accuracy: str
    system_accuracy_index: int
    recommendation: str
    recommendation_index: int
    created_at: datetime
    
    @classmethod
    def create_feedback(cls, user_id: int, frequency_rating: int, frequency_reason: str,
                       explanation_quality_rating: int, explanation_quality_reason: str,
                       system_helpfulness_rating: int, system_helpfulness_reason: str,
                       learning_improvement_rating: int, learning_improvement_reason: str,
                       auto_explanation: bool, auto_reason: str, system_accuracy: str,
                       system_accuracy_index: int, recommendation: str, recommendation_index: int) -> 'ComprehensiveFeedback':
        """Create new comprehensive feedback for research study."""
        return cls(
            id=None,
            user_id=user_id,
            frequency_rating=frequency_rating,
            frequency_reason=frequency_reason,
            explanation_quality_rating=explanation_quality_rating,
            explanation_quality_reason=explanation_quality_reason,
            system_helpfulness_rating=system_helpfulness_rating,
            system_helpfulness_reason=system_helpfulness_reason,
            learning_improvement_rating=learning_improvement_rating,
            learning_improvement_reason=learning_improvement_reason,
            auto_explanation=auto_explanation,
            auto_reason=auto_reason,
            system_accuracy=system_accuracy,
            system_accuracy_index=system_accuracy_index,
            recommendation=recommendation,
            recommendation_index=recommendation_index,
            created_at=datetime.now()
        )
    
    def save(self, db_path: str):
        """Save comprehensive feedback to database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO comprehensive_feedback (
                user_id, frequency_rating, frequency_reason, explanation_quality_rating,
                explanation_quality_reason, system_helpfulness_rating, system_helpfulness_reason,
                learning_improvement_rating, learning_improvement_reason, auto_explanation,
                auto_reason, system_accuracy, system_accuracy_index, recommendation,
                recommendation_index, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.user_id, self.frequency_rating, self.frequency_reason,
            self.explanation_quality_rating, self.explanation_quality_reason,
            self.system_helpfulness_rating, self.system_helpfulness_reason,
            self.learning_improvement_rating, self.learning_improvement_reason,
            self.auto_explanation, self.auto_reason, self.system_accuracy,
            self.system_accuracy_index, self.recommendation, self.recommendation_index,
            self.created_at.isoformat()
        ))
        self.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    @classmethod
    def get_all_feedback(cls, db_path: str) -> List['ComprehensiveFeedback']:
        """Get all comprehensive feedback for admin dashboard."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cf.id, cf.user_id, cf.frequency_rating, cf.frequency_reason,
                   cf.explanation_quality_rating, cf.explanation_quality_reason,
                   cf.system_helpfulness_rating, cf.system_helpfulness_reason,
                   cf.learning_improvement_rating, cf.learning_improvement_reason,
                   cf.auto_explanation, cf.auto_reason, cf.system_accuracy,
                   cf.system_accuracy_index, cf.recommendation, cf.recommendation_index,
                   cf.created_at, u.username
            FROM comprehensive_feedback cf
            JOIN users u ON cf.user_id = u.id
            ORDER BY cf.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback = cls(
                id=row[0], user_id=row[1], frequency_rating=row[2], frequency_reason=row[3],
                explanation_quality_rating=row[4], explanation_quality_reason=row[5],
                system_helpfulness_rating=row[6], system_helpfulness_reason=row[7],
                learning_improvement_rating=row[8], learning_improvement_reason=row[9],
                auto_explanation=bool(row[10]), auto_reason=row[11], system_accuracy=row[12],
                system_accuracy_index=row[13], recommendation=row[14], recommendation_index=row[15],
                created_at=datetime.fromisoformat(row[16])
            )
            # Add username for admin dashboard
            feedback.username = row[17]
            feedback_list.append(feedback)
        
        return feedback_list
    
    @classmethod
    def get_user_feedback(cls, db_path: str, user_id: int) -> Optional['ComprehensiveFeedback']:
        """Get comprehensive feedback for a specific user."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, frequency_rating, frequency_reason, explanation_quality_rating,
                   explanation_quality_reason, system_helpfulness_rating, system_helpfulness_reason,
                   learning_improvement_rating, learning_improvement_reason, auto_explanation,
                   auto_reason, system_accuracy, system_accuracy_index, recommendation,
                   recommendation_index, created_at
            FROM comprehensive_feedback 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row[0], user_id=row[1], frequency_rating=row[2], frequency_reason=row[3],
                explanation_quality_rating=row[4], explanation_quality_reason=row[5],
                system_helpfulness_rating=row[6], system_helpfulness_reason=row[7],
                learning_improvement_rating=row[8], learning_improvement_reason=row[9],
                auto_explanation=bool(row[10]), auto_reason=row[11], system_accuracy=row[12],
                system_accuracy_index=row[13], recommendation=row[14], recommendation_index=row[15],
                created_at=datetime.fromisoformat(row[16])
            )
        return None 