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


# ------------------------------
# Chat sessions (PostgreSQL)
# ------------------------------

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
    def create_session(
        cls,
        user_id: int,
        user_message: str,
        system_response: str,
        sql_query: str = None,
        explanation_given: bool = False,
    ) -> "ChatSession":
        return cls(
            id=None,
            user_id=user_id,
            session_uuid=str(uuid.uuid4()),
            user_message=user_message,
            system_response=system_response,
            sql_query=sql_query,
            explanation_given=explanation_given,
            created_at=datetime.now(),
        )

    def save(self, db_config: Dict[str, Any]):
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (
                    user_id, session_uuid, user_message, system_response,
                    sql_query, explanation_given, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    self.user_id,
                    self.session_uuid,
                    self.user_message,
                    self.system_response,
                    self.sql_query,
                    self.explanation_given,
                    self.created_at,
                ),
            )
            self.id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving chat session: {e}")
            raise

    @classmethod
    def get_user_sessions(
        cls, db_config: Dict[str, Any], user_id: int, limit: int = 50
    ) -> List["ChatSession"]:
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, session_uuid, user_message, system_response,
                       sql_query, explanation_given, created_at
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            sessions: List[ChatSession] = []
            for row in rows:
                sessions.append(
                    cls(
                        id=row[0],
                        user_id=row[1],
                        session_uuid=row[2],
                        user_message=row[3],
                        system_response=row[4],
                        sql_query=row[5],
                        explanation_given=bool(row[6]) if row[6] is not None else False,
                        created_at=row[7]
                        if isinstance(row[7], datetime)
                        else datetime.fromisoformat(str(row[7])),
                    )
                )
            return sessions
        except Exception as e:
            logger.error(f"Error fetching chat sessions: {e}")
            return []

    @classmethod
    def delete_user_sessions(cls, db_config: Dict[str, Any], user_id: int):
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting chat sessions: {e}")
            raise


# ------------------------------------
# Explanation feedback (PostgreSQL)
# ------------------------------------

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
    def create_feedback(
        cls,
        user_id: int,
        session_id: int,
        explanation_given: bool,
        was_needed: bool = None,
        was_helpful: bool = None,
        would_have_been_needed: bool = None,
    ) -> "ExplanationFeedback":
        return cls(
            id=None,
            user_id=user_id,
            session_id=session_id,
            explanation_given=explanation_given,
            was_needed=was_needed,
            was_helpful=was_helpful,
            would_have_been_needed=would_have_been_needed,
            created_at=datetime.now(),
        )

    def save(self, db_config: Dict[str, Any]):
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO explanation_feedback (
                    user_id, session_id, explanation_given,
                    was_needed, was_helpful, would_have_been_needed, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    self.user_id,
                    self.session_id,
                    self.explanation_given,
                    self.was_needed,
                    self.was_helpful,
                    self.would_have_been_needed,
                    self.created_at,
                ),
            )
            self.id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving explanation feedback: {e}")
            raise

    @classmethod
    def get_all_feedback(
        cls, db_config: Dict[str, Any]
    ) -> List["ExplanationFeedback"]:
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ef.id, ef.user_id, ef.session_id, ef.explanation_given,
                       ef.was_needed, ef.was_helpful, ef.would_have_been_needed, ef.created_at,
                       u.username, cs.user_message
                FROM explanation_feedback ef
                JOIN users u ON ef.user_id = u.id
                JOIN chat_sessions cs ON ef.session_id = cs.id
                ORDER BY ef.created_at DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            feedback_list: List[ExplanationFeedback] = []
            for row in rows:
                fb = cls(
                    id=row[0],
                    user_id=row[1],
                    session_id=row[2],
                    explanation_given=bool(row[3]) if row[3] is not None else False,
                    was_needed=bool(row[4]) if row[4] is not None else None,
                    was_helpful=bool(row[5]) if row[5] is not None else None,
                    would_have_been_needed=bool(row[6]) if row[6] is not None else None,
                    created_at=row[7]
                    if isinstance(row[7], datetime)
                    else datetime.fromisoformat(str(row[7])),
                )
                # attach extra fields for dashboard (kept for compatibility)
                setattr(fb, "username", row[8])
                setattr(fb, "user_message", row[9])
                feedback_list.append(fb)
            return feedback_list
        except Exception as e:
            logger.error(f"Error fetching explanation feedback: {e}")
            return []


# --------------------------------------
# Comprehensive feedback (PostgreSQL)
# --------------------------------------

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
    def create_feedback(
        cls,
        user_id: int,
        frequency_rating: int,
        frequency_reason: str,
        explanation_quality_rating: int,
        explanation_quality_reason: str,
        system_helpfulness_rating: int,
        system_helpfulness_reason: str,
        learning_improvement_rating: int,
        learning_improvement_reason: str,
        auto_explanation: bool,
        auto_reason: str,
        system_accuracy: str,
        system_accuracy_index: int,
        recommendation: str,
        recommendation_index: int,
    ) -> "ComprehensiveFeedback":
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
            created_at=datetime.now(),
        )

    def save(self, db_config: Dict[str, Any]):
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO comprehensive_feedback (
                    user_id, frequency_rating, frequency_reason, explanation_quality_rating,
                    explanation_quality_reason, system_helpfulness_rating, system_helpfulness_reason,
                    learning_improvement_rating, learning_improvement_reason, auto_explanation,
                    auto_reason, system_accuracy, system_accuracy_index, recommendation,
                    recommendation_index, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    self.user_id,
                    self.frequency_rating,
                    self.frequency_reason,
                    self.explanation_quality_rating,
                    self.explanation_quality_reason,
                    self.system_helpfulness_rating,
                    self.system_helpfulness_reason,
                    self.learning_improvement_rating,
                    self.learning_improvement_reason,
                    self.auto_explanation,
                    self.auto_reason,
                    self.system_accuracy,
                    self.system_accuracy_index,
                    self.recommendation,
                    self.recommendation_index,
                    self.created_at,
                ),
            )
            self.id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving comprehensive feedback: {e}")
            raise

    @classmethod
    def get_all_feedback(
        cls, db_config: Dict[str, Any]
    ) -> List["ComprehensiveFeedback"]:
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT cf.id, cf.user_id, cf.frequency_rating, cf.frequency_reason,
                       cf.explanation_quality_rating, cf.explanation_quality_reason,
                       cf.system_helpfulness_rating, cf.system_helpfulness_reason,
                       cf.learning_improvement_rating, cf.learning_improvement_reason,
                       cf.auto_explanation, cf.auto_reason, cf.system_accuracy,
                       cf.system_helpfulness_rating, cf.recommendation, cf.recommendation_index,
                       cf.created_at, u.username
                FROM comprehensive_feedback cf
                JOIN users u ON cf.user_id = u.id
                ORDER BY cf.created_at DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            feedback_list: List[ComprehensiveFeedback] = []
            for row in rows:
                fb = cls(
                    id=row[0],
                    user_id=row[1],
                    frequency_rating=row[2],
                    frequency_reason=row[3],
                    explanation_quality_rating=row[4],
                    explanation_quality_reason=row[5],
                    system_helpfulness_rating=row[6],
                    system_helpfulness_reason=row[7],
                    learning_improvement_rating=row[8],
                    learning_improvement_reason=row[9],
                    auto_explanation=bool(row[10]),
                    auto_reason=row[11],
                    system_accuracy=row[12],
                    system_accuracy_index=row[13],
                    recommendation=row[14],
                    recommendation_index=row[15],
                    created_at=row[16]
                    if isinstance(row[16], datetime)
                    else datetime.fromisoformat(str(row[16])),
                )
                setattr(fb, "username", row[17])
                feedback_list.append(fb)
            return feedback_list
        except Exception as e:
            logger.error(f"Error fetching comprehensive feedback: {e}")
            return []

    @classmethod
    def get_user_feedback(
        cls, db_config: Dict[str, Any], user_id: int
    ) -> Optional["ComprehensiveFeedback"]:
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, frequency_rating, frequency_reason, explanation_quality_rating,
                       explanation_quality_reason, system_helpfulness_rating, system_helpfulness_reason,
                       learning_improvement_rating, learning_improvement_reason, auto_explanation,
                       auto_reason, system_accuracy, system_accuracy_index, recommendation,
                       recommendation_index, created_at
                FROM comprehensive_feedback
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                return cls(
                    id=row[0],
                    user_id=row[1],
                    frequency_rating=row[2],
                    frequency_reason=row[3],
                    explanation_quality_rating=row[4],
                    explanation_quality_reason=row[5],
                    system_helpfulness_rating=row[6],
                    system_helpfulness_reason=row[7],
                    learning_improvement_rating=row[8],
                    learning_improvement_reason=row[9],
                    auto_explanation=bool(row[10]),
                    auto_reason=row[11],
                    system_accuracy=row[12],
                    system_accuracy_index=row[13],
                    recommendation=row[14],
                    recommendation_index=row[15],
                    created_at=row[16]
                    if isinstance(row[16], datetime)
                    else datetime.fromisoformat(str(row[16])),
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching user comprehensive feedback: {e}")
            return None
