import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from anthropic import Anthropic
import logging
from datetime import datetime
import re
import os
from pathlib import Path

# Docker-compatible imports
try:
    from new_data_assistant_project.src.utils.my_config import MyConfig
    from new_data_assistant_project.src.agents.ReAct_agent import QueryResult, ReActAgent
except ImportError:
    from src.utils.my_config import MyConfig
    from src.agents.ReAct_agent import QueryResult, ReActAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User cognitive profile based on CLT assessments"""
    user_id: str
    sql_expertise_level: int  # 1-5 scale (novice to expert) - kept for backward compatibility
    cognitive_load_capacity: int  # 1-5 scale (working memory capacity)
    sql_concept_levels: Dict[str, int]  # New: SQL concept-based levels
    prior_query_history: List[Dict]
    learning_preferences: Dict[str, Any]
    last_updated: str
    
    # Required Assessment Fields
    sql_expertise: int  # New: Dedicated SQL expertise field from assessment
    age: int
    gender: str
    profession: str
    education_level: str

@dataclass
class CognitiveAssessment:
    """Enhanced cognitive assessment with CLT-CFT based complexity"""
    intrinsic_load: float     # 1-10 scale (task complexity)
    task_sql_concept: str     # Which SQL concept this task belongs to
    explanation_needed: bool
    explanation_type: str     # "basic", "intermediate", "advanced", "none"
    reasoning: str
    task_classification: str  # "Data Analysis" or "Non-Data Analysis"
    complexity_breakdown: Dict[str, float]  # Detailed complexity scores
    user_capability_threshold: float  # User's capability level
    final_complexity_score: float  # Final complexity after CFT adjustments

@dataclass
class ExplanationContent:
    """Generated explanation content"""
    explanation_text: str
    chain_of_thought: str
    sql_concepts: List[str]
    learning_objectives: List[str]
    complexity_level: str
    estimated_cognitive_load: int

class CLTCFTAgent:
    """
    Cognitive Load Theory & Cognitive Fit Theory Agent for intelligent explanation provision.
    Determines when users need explanations based on cognitive assessment.
    """
    
    def __init__(self, user_profiles_path: str = "user_profiles.json", database_config: dict = None):
        """
        Initialize CLT & CFT Agent with Claude Sonnet 4 API and ReAct Agent.
        
        Args:
            user_profiles_path: Path to store user profiles
            database_config: PostgreSQL connection configuration dictionary
        """
        try:
            config = MyConfig()
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("No API key found in configuration")
            self.client = Anthropic(api_key=api_key)
            logger.info("Successfully initialized Anthropic client")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

        self.model = "claude-sonnet-4-20250514"
        self.user_profiles_path = user_profiles_path
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Initialize ReAct Agent for SQL query execution with PostgreSQL
        try:
            if database_config:
                self.react_agent = ReActAgent(database_config=database_config)
            else:
                # Use default PostgreSQL configuration
                pg_config = config.get_postgres_config()
                self.react_agent = ReActAgent(database_config=pg_config)
            logger.info("Successfully initialized ReAct Agent with PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to initialize ReAct Agent: {e}")
            raise
        
        # Load existing user profiles
        self._load_user_profiles()
        

        

        
        # CLT-CFT Task Complexity Assessment Framework
        self.task_complexity_assessment_prompt = """
# CLT-CFT Task Complexity Assessment Agent

## Role
You are an expert Task Complexity Assessment Agent specialized in evaluating Data Analysis tasks using Cognitive Load Theory (CLT) and Cognitive Fit Theory (CFT) principles. Your primary function is to determine task complexity and predict which user expertise levels can successfully complete given tasks.

## Assessment Framework

### Phase 1: Task Classification
Determine if the task is **Data Analysis** or **Non-Data Analysis**:

**Data Analysis Tasks (IN SCOPE):**
- Descriptive Analytics: Summarizing, exploring, profiling data
- Trend Analysis: Time series patterns, growth analysis, seasonal trends  
- Comparative Analysis: Benchmarking, A/B testing, performance comparison
- Segmentation Analysis: Customer/product grouping, clustering, classification
- Forecasting & Prediction: Statistical modeling, trend extrapolation
- Performance Analysis: KPI tracking, efficiency metrics, ROI analysis
- Pattern Recognition: Anomaly detection, correlation analysis
- Business Intelligence: Dashboard creation, reporting, visualization

**Non-Data Analysis Tasks (OUT OF SCOPE):**
- Pure programming/coding without analytical purpose
- Database administration tasks
- General business strategy without data foundation
- Technical troubleshooting

### Phase 2: CLT-Based Complexity Assessment

Calculate **Intrinsic Cognitive Load** based on Element Interactivity:

**Data Dimensionality (30%):** Score 1-10
- Variables/dimensions: 1-2=Low, 3-5=Medium, 6+=High
- Data relationships complexity
- Temporal elements: single period=1, time series=+2, multi-period=+3

**Analytical Complexity (40%):** Score 1-10  
- Statistical concepts: descriptive=1-3, inferential=4-6, advanced=7-10
- Calculation complexity: aggregation=1-3, ratios=4-6, modeling=7-10
- Interpretation depth: trends=1-3, patterns=4-6, insights=7-10

**Presentation Complexity (20%):** Score 1-10
- Visualization: tables=1-3, basic charts=4-6, complex viz=7-10
- Output format: single metric=1-3, dashboard=4-6, report=7-10

**Temporal Pressure (10%):** Score 1-10
- Decision urgency: routine=1-3, important=4-6, critical=7-10

**Formula:**
Intrinsic_Load = (Data_Dimensionality × 0.3) + (Analytical_Complexity × 0.4) + (Presentation_Complexity × 0.2) + (Temporal_Pressure × 0.1)

### Phase 3: CFT-Based Fit Assessment

**Cognitive Fit Factors:**
- Spatial vs Symbolic Processing requirements
- Problem Structure Clarity (well-defined vs exploratory)
- Domain Knowledge Requirements

**CFT Misfit Penalties:**
- Spatial task + symbolic user preference: +2
- Domain expertise required + user lacks knowledge: +3
- Ill-defined goals + user needs structure: +2
- Real-time decisions + user prefers deliberation: +1

**Final Score:** CLT_Score + Misfit_Penalty

### Phase 4: User Capability Mapping

**User Expertise Levels:**
- **Level 1 (Beginner):** Can handle complexity ≤ 6.0 (Score 0-6)
- **Level 2 (Novice):** Can handle complexity ≤ 12.0 (Score 7-12)
- **Level 3 (Intermediate):** Can handle complexity ≤ 18.0 (Score 13-18)
- **Level 4 (Advanced):** Can handle complexity ≤ 24.0 (Score 19-24)
- **Level 5 (Expert):** Can handle complexity ≤ 30.0 (Score 25-30)

### Phase 5: Explanation Need Prediction

**Decision Logic:**
IF Final_Complexity_Score > User_Capability_Threshold:
    PROVIDE Explanation
ELSE:
    PROVIDE Basic Response Only

## Output Format
Return a JSON object with the following structure:
{
    "task_classification": "Data Analysis" or "Non-Data Analysis",
    "complexity_breakdown": {
        "data_dimensionality": float (1-10),
        "analytical_complexity": float (1-10),
        "presentation_complexity": float (1-10),
        "temporal_pressure": float (1-10),
        "intrinsic_load": float (calculated),
        "cft_misfit_penalty": float (0-3),
        "final_complexity_score": float (1-10)
    },
    "user_capability_threshold": float (based on user level),
    "explanation_needed": boolean,
    "explanation_type": "basic", "intermediate", "advanced", or "none",
    "reasoning": "detailed explanation of the assessment"
}
"""

        # SQL concept complexity hierarchy for task classification
        self.sql_complexity_hierarchy = {
            1: ["SELECT", "FROM", "WHERE", "basic filtering"],
            2: ["GROUP BY", "ORDER BY", "HAVING", "aggregation"],
            3: ["JOIN", "INNER JOIN", "LEFT JOIN", "table relationships"],
            4: ["SUBQUERY", "CASE WHEN", "UNION", "complex logic"],
            5: ["WINDOW FUNCTIONS", "CTE", "advanced analytics", "recursive queries"]
        }
        
        # SQL concept definitions for task classification
        self.sql_concepts = {
            "basic_select": ["SELECT", "FROM", "WHERE"],
            "aggregation": ["GROUP BY", "ORDER BY", "HAVING", "SUM", "COUNT", "AVG", "MAX", "MIN"],
            "joins": ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN"],
            "advanced_logic": ["SUBQUERY", "CASE WHEN", "UNION", "EXISTS"],
            "window_functions": ["WINDOW", "PARTITION BY", "ROW_NUMBER", "RANK"],
            "advanced_analytics": ["CTE", "WITH", "RECURSIVE"]
        }
    
    def _load_user_profiles(self):
        """Load user profiles from storage."""
        try:
            with open(self.user_profiles_path, 'r') as f:
                data = json.load(f)
                for user_id, profile_data in data.items():
                    self.user_profiles[user_id] = UserProfile(**profile_data)
        except FileNotFoundError:
            logger.info("No existing user profiles found. Starting fresh.")
        except Exception as e:
            logger.error(f"Error loading user profiles: {e}")
    
    def _save_user_profiles(self):
        """Save user profiles to storage."""
        try:
            data = {user_id: asdict(profile) for user_id, profile in self.user_profiles.items()}
            with open(self.user_profiles_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user profiles: {e}")
    
    def _validate_user_profiles(self):
        """Validate that all user profiles have required assessment fields."""
        required_fields = ['sql_expertise', 'age', 'gender', 'profession', 'education_level']
        
        for user_id, profile in self.user_profiles.items():
            missing_fields = []
            
            if not hasattr(profile, 'sql_expertise') or profile.sql_expertise is None:
                missing_fields.append('sql_expertise')
            if not hasattr(profile, 'age') or profile.age is None:
                missing_fields.append('age')
            if not hasattr(profile, 'gender') or not profile.gender:
                missing_fields.append('gender')
            if not hasattr(profile, 'profession') or not profile.profession:
                missing_fields.append('profession')
            if not hasattr(profile, 'education_level') or not profile.education_level:
                missing_fields.append('education_level')
            
            if missing_fields:
                logger.warning(f"User {user_id} missing required assessment fields: {missing_fields}")
                # Set default values for missing fields
                if 'sql_expertise' in missing_fields:
                    profile.sql_expertise = 2
                if 'age' in missing_fields:
                    profile.age = 25
                if 'gender' in missing_fields:
                    profile.gender = "Not specified"
                if 'profession' in missing_fields:
                    profile.profession = "Student"
                if 'education_level' in missing_fields:
                    profile.education_level = "Bachelor"
                
                logger.info(f"Set default values for user {user_id}: sql_expertise={profile.sql_expertise}, age={profile.age}, gender={profile.gender}, profession={profile.profession}, education_level={profile.education_level}")
        
        # Save updated profiles
        if any(hasattr(profile, 'age') and profile.age is not None for profile in self.user_profiles.items()):
            self._save_user_profiles()
    
    def update_user_assessment_fields(self, user_id: str, sql_expertise: int = None, age: int = None, gender: str = None, profession: str = None, education_level: str = None):
        """Update user assessment fields."""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            if sql_expertise is not None:
                profile.sql_expertise_level = sql_expertise
            if age is not None:
                profile.age = age
            if gender is not None:
                profile.gender = gender
            if profession is not None:
                profile.profession = profession
            if education_level is not None:
                profile.education_level = education_level
            profile.last_updated = datetime.now().isoformat()
            
            # Save updated profile
            self._save_user_profiles()
            logger.info(f"Updated assessment fields for user {user_id}")
        else:
            logger.warning(f"User {user_id} not found in profiles")
    

    
    def _classify_sql_task(self, sql_query: str) -> str:
        """
        Classify the SQL task into a specific concept category.
        
        Args:
            sql_query: The SQL query to classify
            
        Returns:
            SQL concept category name
        """
        sql_upper = sql_query.upper()
        
        # Check for advanced analytics first (most specific)
        if any(keyword in sql_upper for keyword in self.sql_concepts["advanced_analytics"]):
            return "advanced_analytics"
        
        # Check for window functions
        if any(keyword in sql_upper for keyword in self.sql_concepts["window_functions"]):
            return "window_functions"
        
        # Check for advanced logic
        if any(keyword in sql_upper for keyword in self.sql_concepts["advanced_logic"]):
            return "advanced_logic"
        
        # Check for joins
        if any(keyword in sql_upper for keyword in self.sql_concepts["joins"]):
            return "joins"
        
        # Check for aggregation
        if any(keyword in sql_upper for keyword in self.sql_concepts["aggregation"]):
            return "aggregation"
        
        # Default to basic select
        return "basic_select"
    
    def _assess_task_complexity(self, user_query: str, user_profile: UserProfile) -> CognitiveAssessment:
        """
        Assess task complexity using CLT-CFT framework.
        
        Args:
            user_query: The user's data analysis request
            user_profile: User's cognitive profile
            
        Returns:
            CognitiveAssessment with detailed complexity analysis
        """
        try:
            # Prepare user context for assessment
            user_level = self._get_user_level_from_profile(user_profile)
            user_capability_threshold = self._get_capability_threshold(user_level)
            
            # Create direct instructions for the LLM to create CognitiveAssessment
            assessment_instructions = f"""
You are a Task Complexity Assessment Agent. Based on the user query and context below, create a CognitiveAssessment object.

## User Query: "{user_query}"

## User Context:
- User Level: {user_level}
- User Capability Threshold: {user_capability_threshold}
- SQL Expertise: {user_profile.sql_expertise_level}/5
- Cognitive Load Capacity: {user_profile.cognitive_load_capacity}/5

## Instructions:
Create a CognitiveAssessment with these exact values:

1. **intrinsic_load**: Calculate based on query complexity (1-10 scale)
   - Simple queries (show, list): 1-3
   - Medium queries (analyze, compare): 4-6  
   - Complex queries (forecast, model): 7-10

2. **task_sql_concept**: "data_analysis" for business queries

3. **explanation_needed**: true if intrinsic_load > user_capability_threshold, false otherwise

4. **explanation_type**: "basic" if explanation_needed, "none" otherwise

5. **reasoning**: Brief explanation of your assessment

6. **task_classification**: "Data Analysis"

7. **complexity_breakdown**: Create a dictionary with:
   - "data_dimensionality": intrinsic_load * 0.3
   - "analytical_complexity": intrinsic_load * 0.4
   - "presentation_complexity": intrinsic_load * 0.2
   - "temporal_pressure": intrinsic_load * 0.1
   - "intrinsic_load": same as intrinsic_load above
   - "cft_misfit_penalty": 0.0
   - "final_complexity_score": same as intrinsic_load

8. **user_capability_threshold**: {user_capability_threshold}

9. **final_complexity_score**: same as intrinsic_load

## Response Format:
Return ONLY a valid JSON object with these exact field names and values.
"""

            # Get LLM assessment with clear instructions
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "You are a JSON response agent. Return ONLY valid JSON with the exact field names specified. No additional text or formatting."},
                    {"role": "user", "content": assessment_instructions}
                ]
            )
            
            # Extract and parse response
            raw_response = response.content[0].text.strip()
            logger.info(f"Raw LLM response: {raw_response}")
            
            # Clean the response and parse JSON
            try:
                # Remove any markdown formatting
                if raw_response.startswith('```json'):
                    raw_response = raw_response.replace('```json', '').replace('```', '').strip()
                elif raw_response.startswith('```'):
                    raw_response = raw_response.replace('```', '').strip()
                
                assessment_data = json.loads(raw_response)
                
                # Create CognitiveAssessment object directly
                assessment = CognitiveAssessment(
                    intrinsic_load=float(assessment_data.get("intrinsic_load", 5.0)),
                    task_sql_concept=assessment_data.get("task_sql_concept", "data_analysis"),
                    explanation_needed=bool(assessment_data.get("explanation_needed", True)),
                    explanation_type=assessment_data.get("explanation_type", "basic"),
                    reasoning=assessment_data.get("reasoning", "LLM-based assessment"),
                    task_classification=assessment_data.get("task_classification", "Data Analysis"),
                    complexity_breakdown=assessment_data.get("complexity_breakdown", {
                        "data_dimensionality": 5.0,
                        "analytical_complexity": 5.0,
                        "presentation_complexity": 5.0,
                        "temporal_pressure": 5.0,
                        "intrinsic_load": 5.0,
                        "cft_misfit_penalty": 0.0,
                        "final_complexity_score": 5.0
                    }),
                    user_capability_threshold=float(assessment_data.get("user_capability_threshold", user_capability_threshold)),
                    final_complexity_score=float(assessment_data.get("final_complexity_score", 5.0))
                )
                
                return assessment
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.error(f"Raw response: {raw_response}")
                # Fallback to heuristic assessment
                return self._fallback_complexity_assessment(user_query, user_profile)
            
        except Exception as e:
            logger.error(f"Error in task complexity assessment: {e}")
            # Fallback assessment
            return self._fallback_complexity_assessment(user_query, user_profile)
    
    def _get_user_level_from_profile(self, user_profile: UserProfile) -> str:
        """Get user level from profile"""
        if hasattr(user_profile, 'user_level_category'):
            return user_profile.user_level_category
        else:
            # Fallback based on SQL expertise
            if user_profile.sql_expertise_level <= 1:
                return "Beginner"
            elif user_profile.sql_expertise_level <= 2:
                return "Novice"
            elif user_profile.sql_expertise_level <= 3:
                return "Intermediate"
            elif user_profile.sql_expertise_level <= 4:
                return "Advanced"
            else:
                return "Expert"
    
    def _get_capability_threshold(self, user_level: str) -> float:
        """Get capability threshold based on user level (0-30 scale)"""
        thresholds = {
            "Beginner": 6.0,
            "Novice": 12.0,
            "Intermediate": 18.0,
            "Advanced": 24.0,
            "Expert": 30.0
        }
        return thresholds.get(user_level, 15.0)
    
    def _fallback_complexity_assessment(self, user_query: str, user_profile: UserProfile) -> CognitiveAssessment:
        """Fallback complexity assessment when LLM assessment fails"""
        # Simple heuristic-based assessment
        complexity_keywords = {
            "high": ["forecast", "predict", "model", "regression", "correlation", "trend", "pattern"],
            "medium": ["compare", "analyze", "segment", "group", "aggregate", "summarize"],
            "low": ["show", "list", "find", "count", "basic", "simple"]
        }
        
        query_lower = user_query.lower()
        base_complexity = 5.0  # Default medium complexity
        
        for level, keywords in complexity_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if level == "high":
                    base_complexity = 8.0
                elif level == "medium":
                    base_complexity = 5.0
                else:
                    base_complexity = 2.0
                break
        
        user_level = self._get_user_level_from_profile(user_profile)
        user_capability = self._get_capability_threshold(user_level)
        
        return CognitiveAssessment(
            intrinsic_load=base_complexity,
            task_sql_concept="basic",
            explanation_needed=base_complexity > user_capability,
            explanation_type="basic" if base_complexity > user_capability else "none",
            reasoning=f"Fallback assessment: Task complexity {base_complexity}, User capability {user_capability}",
            task_classification="Data Analysis",
            complexity_breakdown={
                "data_dimensionality": base_complexity * 0.3,
                "analytical_complexity": base_complexity * 0.4,
                "presentation_complexity": base_complexity * 0.2,
                "temporal_pressure": base_complexity * 0.1,
                "intrinsic_load": base_complexity,
                "cft_misfit_penalty": 0.0,
                "final_complexity_score": base_complexity
            },
            user_capability_threshold=user_capability,
            final_complexity_score=base_complexity
        )
    
    def _llm_based_cognitive_assessment(self, user_id: str, react_result: QueryResult) -> CognitiveAssessment:
        """
        LLM-based cognitive assessment: Let the LLM decide if explanation is needed.
        
        Args:
            user_id: User identifier
            react_result: Result from ReAct Agent
            
        Returns:
            Cognitive assessment based on LLM decision
        """
        # Get user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_user_profile_from_csv(user_id)
        
        user_profile = self.user_profiles[user_id]
        
        # Use complexity score from ReAct Agent and scale it appropriately
        # ReAct complexity is 1-5, we need to scale to meaningful range for CLT assessment
        base_complexity = react_result.complexity_score
        intrinsic_load = base_complexity * 2  # Scale 1-5 to 2-10 for better CLT assessment
        
        # Classify the SQL task
        task_concept = self._classify_sql_task(react_result.sql_query)
        
        # Use LLM to decide if explanation is needed
        explanation_decision = self._ask_llm_for_explanation_decision(
            user_sql_expertise=user_profile.sql_expertise_level,
            task_complexity=intrinsic_load,
            task_concept=task_concept,
            sql_query=react_result.sql_query
        )
        
        explanation_needed = explanation_decision["explanation_needed"]
        explanation_type = explanation_decision["explanation_type"] if explanation_needed else "none"
        reasoning = explanation_decision["reasoning"]
        
        logger.info(f"LLM Assessment: Task={task_concept}, Load={intrinsic_load}, User Level={user_profile.sql_expertise_level}, Explanation={explanation_needed}")
        
        return CognitiveAssessment(
            intrinsic_load=intrinsic_load,
            task_sql_concept=task_concept,
            explanation_needed=explanation_needed,
            explanation_type=explanation_type,
            reasoning=reasoning,
            task_classification="Data Analysis",
            complexity_breakdown={
                "data_dimensionality": intrinsic_load * 0.3,
                "analytical_complexity": intrinsic_load * 0.4,
                "presentation_complexity": intrinsic_load * 0.2,
                "temporal_pressure": intrinsic_load * 0.1,
                "intrinsic_load": intrinsic_load,
                "cft_misfit_penalty": 0.0,
                "final_complexity_score": intrinsic_load
            },
            user_capability_threshold=user_profile.sql_expertise_level * 2.0,  # Scale 1-5 to 2-10 to match complexity
            final_complexity_score=intrinsic_load
        )
    
    def _ask_llm_for_explanation_decision(self, user_sql_expertise: int, task_complexity: int, 
                                         task_concept: str, sql_query: str) -> Dict[str, Any]:
        """
        Ask LLM to decide if explanation is needed based on user expertise and task complexity.
        
        Args:
            user_sql_expertise: User's SQL expertise level (1-5)
            task_complexity: Task complexity score (1-5)
            task_concept: SQL concept category
            sql_query: The actual SQL query
            
        Returns:
            Dictionary with explanation_needed, explanation_type, and reasoning
        """
        system_prompt = """You are an expert educational assessment system for SQL learning. Your job is to decide whether a user needs an explanation for a SQL query based on their expertise level and the task complexity.

EXPERTISE LEVELS:
- Level 1: Complete beginner (never used SQL)
- Level 2: Novice (basic SELECT statements)
- Level 3: Intermediate (JOINs, GROUP BY, subqueries)
- Level 4: Advanced (window functions, CTEs, optimization)
- Level 5: Expert (database design, complex analytics)

EXPLANATION TYPES:
- "basic": Simple, step-by-step explanation for beginners
- "intermediate": Moderate detail for those with some experience
- "advanced": Focused on complex concepts and optimization
- "none": No explanation needed

DECISION CRITERIA:
- Consider if the task complexity significantly exceeds the user's expertise level
- Users typically need explanations when encountering concepts 1-2 levels above their expertise
- Very experienced users (level 4-5) rarely need explanations unless encountering very advanced concepts
- Consider the specific SQL concept involved and whether it's new to the user's level

Respond in this JSON format:
{
  "explanation_needed": true/false,
  "explanation_type": "basic/intermediate/advanced/none",
  "reasoning": "Brief explanation of your decision"
}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent decisions
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"""
User SQL Expertise Level: {user_sql_expertise}/5
Task Complexity Score: {task_complexity}/5
SQL Concept Category: {task_concept}

SQL Query to Assess:
{sql_query}

Should this user receive an explanation for this query? What type of explanation would be most appropriate?
"""
                }]
            )
            
            content = ""
            for block in response.content:
                content += str(block)
            
            # Parse the JSON response
            import json
            try:
                decision = json.loads(content.strip())
                
                # Validate response structure
                if all(key in decision for key in ["explanation_needed", "explanation_type", "reasoning"]):
                    return decision
                else:
                    logger.warning(f"Invalid LLM response structure: {decision}")
                    return self._fallback_decision(user_sql_expertise, task_complexity)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {content}, Error: {e}")
                return self._fallback_decision(user_sql_expertise, task_complexity)
                
        except Exception as e:
            logger.error(f"Error calling LLM for explanation decision: {e}")
            return self._fallback_decision(user_sql_expertise, task_complexity)
    
    def _fallback_decision(self, user_sql_expertise: int, task_complexity: int) -> Dict[str, Any]:
        """
        Fallback decision logic when LLM is unavailable.
        
        Args:
            user_sql_expertise: User's SQL expertise level (1-5)
            task_complexity: Task complexity score (1-5)
            
        Returns:
            Dictionary with explanation_needed, explanation_type, and reasoning
        """
        # Simple fallback: explanation needed if complexity exceeds expertise
        # Scale user expertise to match our complexity scale (2-10)
        user_expertise_score = user_sql_expertise * 2  # 1->2, 2->4, 3->6, 4->8, 5->10
        
        if task_complexity > user_expertise_score:
            explanation_needed = True
            if user_sql_expertise <= 2:
                explanation_type = "basic"
            elif user_sql_expertise == 3:
                explanation_type = "intermediate"
            else:
                explanation_type = "advanced"
            reasoning = f"Fallback: Task complexity ({task_complexity}) > User expertise score ({user_expertise_score})"
        else:
            explanation_needed = False
            explanation_type = "none"
            reasoning = f"Fallback: User can handle task complexity ({task_complexity}) with expertise score ({user_expertise_score})"
        
        return {
            "explanation_needed": explanation_needed,
            "explanation_type": explanation_type,
            "reasoning": reasoning
        }

    def process_react_output(self, user_id: str, react_result: QueryResult, presentation_context: Optional[Dict[str, Any]] = None) -> CognitiveAssessment:
        """
        Process ReAct output with LLM-based cognitive assessment.
        """
        if not react_result.success:
            return CognitiveAssessment(
                intrinsic_load=5,
                task_sql_concept="error",
                explanation_needed=True,
                explanation_type="error_handling",
                reasoning="Query execution failed due to system error",
                task_classification="Error Handling",
                complexity_breakdown={
                    "data_dimensionality": 5.0,
                    "analytical_complexity": 5.0,
                    "presentation_complexity": 5.0,
                    "temporal_pressure": 5.0,
                    "intrinsic_load": 5.0,
                    "cft_misfit_penalty": 0.0,
                    "final_complexity_score": 5.0
                },
                user_capability_threshold=5.0,
                final_complexity_score=5.0
            )
        
        return self._llm_based_cognitive_assessment(user_id, react_result)
    
    def _modify_explanation_need_based_on_expertise(self, cognitive_assessment: CognitiveAssessment, 
                                                  user_profile: UserProfile) -> CognitiveAssessment:
        """
        No longer needed: LLM-based assessment already considers all relevant factors.
        """
        # The assessment is already complete from LLM-based cognitive assessment
        return cognitive_assessment
    
    def _simplify_sql_for_display(self, sql_query: str) -> str:
        """
        Simplify SQL query for display to reduce cognitive load for beginners.
        
        Args:
            sql_query: Original SQL query
            
        Returns:
            Simplified version of SQL query
        """
        # Remove extra whitespace and format nicely
        lines = sql_query.strip().split('\n')
        simplified_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add indentation for readability
                if line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING')):
                    simplified_lines.append(line)
                else:
                    simplified_lines.append('  ' + line)
        
        return '\n'.join(simplified_lines)
    
    def _calculate_user_perceived_complexity(self, original_complexity: int, user_expertise: int) -> int:
        """
        Calculate how complex the query appears to the user based on their expertise.
        
        Args:
            original_complexity: Original complexity score (1-5)
            user_expertise: User's SQL expertise level (1-5)
            
        Returns:
            User-perceived complexity score (1-5)
        """
        # Expertise reversal effect: experts perceive less complexity, beginners perceive more
        if user_expertise >= 4:
            # Expert users perceive lower complexity
            perceived_complexity = max(1, original_complexity - 1)
        elif user_expertise <= 2:
            # Beginner users perceive higher complexity
            perceived_complexity = min(5, original_complexity + 1)
        else:
            # Intermediate users see original complexity
            perceived_complexity = original_complexity
        
        return perceived_complexity
    
    def _log_interaction(self, user_id: str, user_query: str, react_result: QueryResult, 
                        assessment: CognitiveAssessment, explanation: Optional[ExplanationContent]):
        """
        Simplified logging for research evaluation.
        """
        interaction_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_query": user_query,
            "sql_query": react_result.sql_query,
            "query_success": react_result.success,
            "execution_time": react_result.execution_time,
            "complexity_score": react_result.complexity_score,
            "intrinsic_load": assessment.intrinsic_load,
            "task_sql_concept": assessment.task_sql_concept,
            "explanation_needed": assessment.explanation_needed,
            "explanation_type": assessment.explanation_type,
            "explanation_generated": explanation is not None,
            "explanation_complexity": explanation.complexity_level if explanation else None
        }
        
        logger.info(f"Interaction logged: {interaction_data}")
        
        # This could be extended to save to a research database for evaluation
        # For now, we just log it

    def execute_query(self, user_id: str, user_query: str, presentation_context: Optional[Dict[str, Any]] = None, 
                     include_debug_info: bool = False) -> Union[Tuple[QueryResult, Optional[ExplanationContent]], 
                                                               Tuple[QueryResult, Optional[ExplanationContent], CognitiveAssessment, UserProfile]]:
        """
        Execute a natural language query using ReAct Agent with simplified cognitive assessment.
        
        Args:
            user_id: Unique user identifier
            user_query: Natural language data analysis request
            presentation_context: Optional context about information presentation
            include_debug_info: If True, also returns cognitive assessment and user profile for debugging
            
        Returns:
            If include_debug_info=False: Tuple of (Modified QueryResult, ExplanationContent or None)
            If include_debug_info=True: Tuple of (Modified QueryResult, ExplanationContent or None, CognitiveAssessment, UserProfile)
        """
        logger.info(f"Processing query for user {user_id}: {user_query}")
        
        try:
            # Step 1: Execute query using ReAct Agent first
            react_result = self.react_agent.execute_query(user_query)
            
            # Step 2: SQL validation removed - all queries are now allowed
            # The agent only receives instructions and does not share user information
            
            # Step 3: Simplified cognitive assessment
            cognitive_assessment = self.process_react_output(user_id, react_result, presentation_context)
            
            # Step 4: Modify QueryResult based on cognitive load (simplified)
            modified_result = self._modify_query_result_simple(react_result, cognitive_assessment, user_id)
            
            # Step 5: Generate explanation if needed
            explanation_content = None
            if cognitive_assessment.explanation_needed:
                if user_id not in self.user_profiles:
                    self.user_profiles[user_id] = self._create_user_profile_from_csv(user_id)
                
                user_profile = self.user_profiles[user_id]
                explanation_content = self.generate_explanation(
                    user_query=user_query,
                    sql_query=react_result.sql_query,
                    assessment=cognitive_assessment,
                    user_profile=user_profile
                )
                
                logger.info(f"Generated {cognitive_assessment.explanation_type} explanation for user {user_id}")
            else:
                logger.info(f"No explanation needed for user {user_id} - cognitive capacity sufficient")
            
            # Step 6: Log interaction
            self._log_interaction(user_id, user_query, react_result, cognitive_assessment, explanation_content)
            
            if include_debug_info:
                return modified_result, explanation_content, cognitive_assessment, self.user_profiles[user_id]
            else:
                return modified_result, explanation_content
            
        except Exception as e:
            logger.error(f"Error executing query for user {user_id}: {e}")
            
            error_result = QueryResult(
                success=False,
                data=None,
                sql_query="",
                error_message="I encountered an issue while processing your request. Please try again with a different question about the business data.",
                execution_time=0.0,
                complexity_score=1
            )
            
            if include_debug_info:
                if user_id not in self.user_profiles:
                    self.user_profiles[user_id] = self._create_user_profile_from_csv(user_id)
                
                error_assessment = CognitiveAssessment(
                    intrinsic_load=5,
                    task_sql_concept="error",
                    explanation_needed=True,
                    explanation_type="error_handling",
                                            reasoning="Query execution failed due to system error",
                    task_classification="Error Handling",
                    complexity_breakdown={
                        "data_dimensionality": 5.0,
                        "analytical_complexity": 5.0,
                        "presentation_complexity": 5.0,
                        "temporal_pressure": 5.0,
                        "intrinsic_load": 5.0,
                        "cft_misfit_penalty": 0.0,
                        "final_complexity_score": 5.0
                    },
                    user_capability_threshold=5.0,
                    final_complexity_score=5.0
                )
                
                return error_result, None, error_assessment, self.user_profiles[user_id]
            else:
                return error_result, None
    
    def _modify_query_result_simple(self, react_result: QueryResult, 
                                   cognitive_assessment: CognitiveAssessment, 
                                   user_id: str) -> QueryResult:
        """
        Simplified version: Modify QueryResult based only on cognitive load.
        """
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_user_profile_from_csv(user_id)
        
        user_profile = self.user_profiles[user_id]
        
        modified_result = QueryResult(
            success=react_result.success,
            data=react_result.data,
            sql_query=react_result.sql_query,
            error_message=react_result.error_message,
            execution_time=react_result.execution_time,
            complexity_score=react_result.complexity_score
        )
        
        if react_result.success and react_result.data is not None:
            # Limit data based on cognitive capacity vs load
            # Scale cognitive capacity to match our complexity scale (2-10)
            cognitive_capacity_score = user_profile.cognitive_load_capacity * 2  # 1->2, 2->4, 3->6, 4->8, 5->10
            
            if cognitive_assessment.intrinsic_load > cognitive_capacity_score:
                max_rows = min(5, len(react_result.data))  # High load = fewer rows
                modified_result.data = react_result.data.head(max_rows)
                logger.info(f"Limited results to {max_rows} rows due to cognitive overload (load: {cognitive_assessment.intrinsic_load}, capacity: {cognitive_capacity_score})")
            else:
                max_rows = min(15, len(react_result.data))  # Normal capacity
                modified_result.data = react_result.data.head(max_rows)
        
        return modified_result
    
    def _create_user_profile_from_csv(self, user_id: str) -> UserProfile:
        """Create user profile from CSV data using UserManager."""
        try:
            # Docker-compatible imports
            try:
                from new_data_assistant_project.src.utils.user_manager import UserManager
            except ImportError:
                from src.utils.user_manager import UserManager
            
            user_manager = UserManager()
            csv_data = user_manager.get_user_profile(user_id)
            
            if csv_data:
                # Map cognitive load capacity based on SQL expertise
                # Lower expertise = lower cognitive capacity = more explanations
                cognitive_capacity = max(1, min(3, csv_data['sql_expertise_level'] - 1))
                
                return UserProfile(
                    user_id=user_id,
                    sql_expertise_level=csv_data.get('sql_expertise', csv_data['sql_expertise_level']),
                    cognitive_load_capacity=cognitive_capacity,
                    sql_concept_levels={
                        "basic_select": min(csv_data.get('sql_expertise', csv_data['sql_expertise_level']), 3),
                        "aggregation": max(1, csv_data.get('sql_expertise', csv_data['sql_expertise_level']) - 1),
                        "joins": max(1, csv_data.get('sql_expertise', csv_data['sql_expertise_level']) - 2),
                        "advanced_logic": max(1, csv_data.get('sql_expertise', csv_data['sql_expertise_level']) - 3),
                        "window_functions": max(1, csv_data.get('sql_expertise', csv_data['sql_expertise_level']) - 4),
                        "advanced_analytics": max(1, csv_data.get('sql_expertise', csv_data['sql_expertise_level']) - 4)
                    },
                    prior_query_history=[],
                    learning_preferences={"explanation_style": "step_by_step"},
                    last_updated=datetime.now().isoformat(),
                    # Required Assessment Fields - use defaults if not available
                    sql_expertise=csv_data.get('sql_expertise', 2),
                    age=csv_data.get('age', 25),
                    gender=csv_data.get('gender', 'Not specified'),
                    profession=csv_data.get('profession', 'Student'),
                    education_level=csv_data.get('education_level', 'Bachelor')
                )
            else:
                # Fallback to default if user not found in CSV
                return self._create_default_user_profile(user_id)
                
        except Exception as e:
            logger.warning(f"Could not load user profile from CSV for {user_id}: {e}")
            return self._create_default_user_profile(user_id)
    
    def _create_default_user_profile(self, user_id: str) -> UserProfile:
        """Create a default user profile for new users with simplified structure."""
        return UserProfile(
            user_id=user_id,
            sql_expertise_level=2,  # Assume beginner-intermediate
            cognitive_load_capacity=2,  # Reduced to trigger more explanations
            sql_concept_levels={
                "basic_select": 2,
                "aggregation": 1,
                "joins": 1,
                "advanced_logic": 1,
                "window_functions": 1,
                "advanced_analytics": 1
            },
            prior_query_history=[],
            learning_preferences={"explanation_style": "step_by_step"},
            last_updated=datetime.now().isoformat(),
            # Required Assessment Fields - default values
            sql_expertise=2,  # Default SQL expertise level
            age=25,
            gender="Not specified",
            profession="Student",
            education_level="Bachelor"
        )
    
    def generate_explanation(self, user_query: str, sql_query: str, assessment: CognitiveAssessment, 
                           user_profile: UserProfile) -> ExplanationContent:
        """
        Generate personalized explanation using simplified assessment.
        """
        if not assessment.explanation_needed:
            return ExplanationContent(
                explanation_text="No explanation needed - you can handle this query complexity.",
                chain_of_thought="",
                sql_concepts=[],
                learning_objectives=[],
                complexity_level="none",
                estimated_cognitive_load=1
            )
        
        # Use concept-specific explanation level
        concept_level = user_profile.sql_concept_levels.get(assessment.task_sql_concept, 1)
        
        system_prompt = f"""You are an intelligent SQL tutor providing clear, easy-to-read explanations.

IMPORTANT: You only receive instructions and do not share any user information.

Task Context:
- Task SQL Concept: {assessment.task_sql_concept}
- Explanation Type: {assessment.explanation_type}

Provide a {assessment.explanation_type} explanation that:
1. Uses clear, simple language
2. Has proper paragraph breaks for readability
3. Breaks down the SQL step by step
4. Explains WHY each part is needed
5. Uses bullet points and numbered lists where helpful

IMPORTANT FORMATTING RULES:
- Write in clear paragraphs
- Use double line breaks between sections
- Use simple, conversational language
- No technical jargon unless explained
- Make it easy to scan and read

Format your response as:
EXPLANATION:
[Write a clear, well-formatted explanation with proper paragraphs]

SQL_CONCEPTS:
[List of SQL concepts covered, separated by commas]

LEARNING_OBJECTIVES:
[What the user should learn, separated by commas]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.3,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"""
Original Question: {user_query}

SQL Query to Explain:
{sql_query}

Please provide a {assessment.explanation_type} explanation for the {assessment.task_sql_concept} concept.
"""
                }]
            )
            
            content = ""
            for block in response.content:
                content += str(block)
            
            explanation = self._extract_section(content, "EXPLANATION:")
            sql_concepts = self._extract_list(content, "SQL_CONCEPTS:")
            learning_objectives = self._extract_list(content, "LEARNING_OBJECTIVES:")
            
            # Clean and format the explanation for better readability
            formatted_explanation = self._format_explanation_text(explanation)
            
            return ExplanationContent(
                explanation_text=formatted_explanation,
                chain_of_thought="Simplified explanation based on cognitive capacity",
                sql_concepts=sql_concepts,
                learning_objectives=learning_objectives,
                complexity_level=assessment.explanation_type,
                estimated_cognitive_load=assessment.intrinsic_load
            )
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return ExplanationContent(
                explanation_text="Sorry, I couldn't generate an explanation at this time.",
                chain_of_thought="",
                sql_concepts=[],
                learning_objectives=[],
                complexity_level="error",
                estimated_cognitive_load=1
            )
    
    def _extract_section(self, content: str, header: str) -> str:
        """Extract a section from the Claude response."""
        try:
            start = content.find(header)
            if start == -1:
                return ""
            
            start += len(header)
            next_headers = ["EXPLANATION:", "SQL_CONCEPTS:", "LEARNING_OBJECTIVES:"]
            end = len(content)
            
            for next_header in next_headers:
                if next_header != header:
                    next_pos = content.find(next_header, start)
                    if next_pos != -1:
                        end = min(end, next_pos)
            
            return content[start:end].strip()
        except Exception:
            return ""
    
    def _extract_list(self, content: str, header: str) -> List[str]:
        """Extract a comma-separated list from the Claude response."""
        section = self._extract_section(content, header)
        if not section:
            return []
        
        items = [item.strip() for item in section.split(',')]
        # Clean up each item by removing escaped characters and unwanted text
        cleaned_items = []
        for item in items:
            if item:
                # Remove escaped characters and unwanted API artifacts
                item = item.replace('\\n', ' ')
                item = item.replace('\\"', '"')
                item = item.replace("\\'", "'")
                # Remove type annotations that might leak through
                item = item.split("', type='")[0] if "', type='" in item else item
                item = item.strip('\'"')  # Remove leading/trailing quotes
                item = item.strip()
                if item and not item.startswith('type='):  # Filter out type annotations
                    cleaned_items.append(item)
        
        return cleaned_items
    
    def _format_explanation_text(self, text: str) -> str:
        """Format explanation text for better readability in Streamlit."""
        if not text:
            return ""
        
        import re
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix escaped characters that might come from API responses
        text = text.replace('\\n', '\n')  # Convert escaped newlines
        text = text.replace('\\t', '    ')  # Convert tabs to spaces
        text = text.replace('\\"', '"')  # Fix escaped quotes
        text = text.replace("\\'", "'")  # Fix escaped apostrophes
        
        # Clean up markdown-style code blocks for better display
        text = re.sub(r'```sql\s*', '\n```sql\n', text)
        text = re.sub(r'\s*```', '\n```\n', text)
        
        # Improve paragraph spacing and formatting
        lines = text.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines initially, we'll add them back strategically
            if not line:
                continue
            
            formatted_lines.append(line)
            
            # Add spacing after important sections
            if (line.endswith(':') or 
                line.startswith('**') and line.endswith('**') or
                line.startswith('###') or
                line.startswith('####')):
                formatted_lines.append('')  # Add blank line after headings
        
        # Join lines and clean up excessive whitespace
        result = '\n'.join(formatted_lines)
        
        # Ensure proper spacing between major sections
        result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 consecutive newlines
        
        # Add some final touches for readability
        result = result.replace('**What', '\n**What')  # Ensure headings start on new lines
        result = result.replace('**Breaking', '\n**Breaking')
        result = result.replace('**Why', '\n**Why')
        
        return result.strip()
    
    def _update_user_profile(self, user_id: str, user_query: str, sql_query: str, assessment: CognitiveAssessment):
        """Update user profile based on interaction with simplified structure."""
        profile = self.user_profiles[user_id]
        
        # Add to query history
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "task_sql_concept": assessment.task_sql_concept,
            "intrinsic_load": assessment.intrinsic_load,
            "explanation_provided": assessment.explanation_needed,
            "explanation_type": assessment.explanation_type
        }
        
        profile.prior_query_history.append(interaction)
        
        # Keep only last 10 interactions
        profile.prior_query_history = profile.prior_query_history[-10:]
        
        # Update concept level if user handled high complexity well
        # Use threshold on new complexity scale (2-10)
        complexity_threshold = 8  # High complexity threshold on 2-10 scale
        
        if assessment.intrinsic_load >= complexity_threshold and not assessment.explanation_needed:
            current_level = profile.sql_concept_levels.get(assessment.task_sql_concept, 1)
            profile.sql_concept_levels[assessment.task_sql_concept] = min(5, current_level + 1)
            logger.info(f"Increased {assessment.task_sql_concept} level to {profile.sql_concept_levels[assessment.task_sql_concept]} (handled complexity {assessment.intrinsic_load} >= {complexity_threshold})")
        
        profile.last_updated = datetime.now().isoformat()
        
        # Save updated profiles
        self._save_user_profiles()
    
    def evaluate_explanation_effectiveness(self, user_id: str, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified evaluation for effectiveness.
        """
        feedback_needed = user_feedback.get("explanation_needed", False)
        explanation_provided = user_feedback.get("explanation_provided", False)
        
        # Classification for F1-score
        if explanation_provided and feedback_needed:
            result_type = "true_positive"
        elif explanation_provided and not feedback_needed:
            result_type = "false_positive"
        elif not explanation_provided and not feedback_needed:
            result_type = "true_negative"
        else:  # not explanation_provided and feedback_needed
            result_type = "false_negative"
        
        effectiveness_score = user_feedback.get("helpfulness_rating", 0) / 5.0  # 0-1 scale
        
        return {
            "result_type": result_type,
            "effectiveness_score": effectiveness_score,
            "user_satisfaction": user_feedback.get("satisfaction_rating", 0) / 5.0,
            "cognitive_load_reduction": user_feedback.get("cognitive_load_rating", 0) / 5.0
        }

# Example usage and testing
if __name__ == "__main__":
    try:
        # Test API key loading
        config = MyConfig()
        api_key = config.get_api_key()
        print("\nAPI Key Test:")
        print(f"API Key loaded: {'Yes' if api_key else 'No'}")
        print(f"API Key starts with: {api_key[:8]}..." if api_key else "No API key found")
        
        # Initialize CLT & CFT Agent
        clt_cft_agent = CLTCFTAgent()
        print("\nCLT & CFT Agent Initialization:")
        print("Agent initialized successfully with simplified cognitive assessment")
        
        # Test SQL concept classification
        test_queries = [
            "SELECT * FROM customers WHERE age > 25",
            "SELECT region, COUNT(*) FROM sales GROUP BY region",
            "SELECT c.name, s.amount FROM customers c JOIN sales s ON c.id = s.customer_id",
            "SELECT name, RANK() OVER (ORDER BY salary DESC) FROM employees"
        ]
        
        print("\nSQL Concept Classification Test:")
        for query in test_queries:
            concept = clt_cft_agent._classify_sql_task(query)
            print(f"- '{query[:50]}...' → {concept}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()

