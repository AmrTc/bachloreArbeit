import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from anthropic import Anthropic
import logging
from datetime import datetime, timedelta
import re
import os
from pathlib import Path
import hashlib
import threading
from functools import lru_cache
import time

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
    sql_expertise_level: int  # 1-5 scale
    cognitive_load_capacity: int  # 1-5 scale
    sql_concept_levels: Dict[str, int]
    prior_query_history: List[Dict]
    learning_preferences: Dict[str, Any]
    last_updated: str
    
    # Required Assessment Fields
    sql_expertise: int
    age: int
    gender: str
    profession: str
    education_level: str

@dataclass
class CognitiveAssessment:
    """Enhanced cognitive assessment with CLT-CFT based complexity"""
    intrinsic_load: float
    task_sql_concept: str
    explanation_needed: bool
    explanation_type: str
    reasoning: str
    task_classification: str
    complexity_breakdown: Dict[str, float]
    user_capability_threshold: float
    final_complexity_score: float

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
    Optimized Cognitive Load Theory & Cognitive Fit Theory Agent 
    using Anthropic Claude API best practices.
    """
    
    def __init__(self, user_profiles_path: str = "user_profiles.json", 
                 database_config: dict = None, 
                 enable_caching: bool = True):
        """
        Initialize CLT-CFT Agent with Anthropic best practices.
        """
        self.enable_caching = enable_caching
        
        # Initialize Anthropic client with best practices
        try:
            api_key = self._get_api_key()
            if not api_key:
                raise ValueError("No API key found in configuration")
            
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-20250514"  # Latest model with Extended Thinking support
            
            logger.info(f"✅ Initialized Anthropic client with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
        
        self.user_profiles_path = user_profiles_path
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Initialize ReAct Agent
        try:
            db_config = database_config or self._get_database_config()
            self.react_agent = ReActAgent(database_config=db_config, enable_caching=enable_caching)
            logger.info("✅ Successfully initialized ReAct Agent")
        except Exception as e:
            logger.error(f"Failed to initialize ReAct Agent: {e}")
            raise
        
        # Load user profiles
        self._load_user_profiles()
        
        # SQL concept hierarchy
        self.sql_concepts = {
            "basic_select": ["SELECT", "FROM", "WHERE"],
            "aggregation": ["GROUP BY", "ORDER BY", "HAVING", "SUM", "COUNT", "AVG"],
            "joins": ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN"],
            "advanced_logic": ["SUBQUERY", "CASE WHEN", "UNION", "EXISTS"],
            "window_functions": ["WINDOW", "PARTITION BY", "ROW_NUMBER", "RANK"],
            "advanced_analytics": ["CTE", "WITH", "RECURSIVE"]
        }
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key with fallback methods."""
        # Method 1: Environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Method 2: From config
        if not api_key:
            try:
                config = MyConfig()
                api_key = config.get_api_key()
            except:
                pass
        
        return api_key
    
    def _get_database_config(self) -> dict:
        """Get database configuration."""
        try:
            config = MyConfig()
            return config.get_postgres_config()
        except:
            # Fallback configuration
            return {
                'host': '34.59.248.159',
                'port': 5432,
                'database': 'superstore',
                'user': 'postgres',
                'password': 'RHGAgo4<C4fyr',
                'sslmode': 'require'
            }
    
    def _load_user_profiles(self):
        """Load user profiles from storage."""
        try:
            with open(self.user_profiles_path, 'r') as f:
                data = json.load(f)
                for user_id, profile_data in data.items():
                    self.user_profiles[user_id] = UserProfile(**profile_data)
            logger.info(f"Loaded {len(self.user_profiles)} user profiles")
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
    
    def _classify_sql_task(self, sql_query: str) -> str:
        """Classify SQL task into concept category."""
        if not sql_query:
            return "basic_select"
        
        sql_upper = sql_query.upper()
        
        # Check concepts from most to least complex
        for concept_name, keywords in reversed(list(self.sql_concepts.items())):
            if any(keyword in sql_upper for keyword in keywords):
                return concept_name
        
        return "basic_select"
    
    def _assess_task_complexity_optimized(self, user_query: str, user_profile: UserProfile) -> CognitiveAssessment:
        """
        Assess task complexity using optimized Claude API call with structured prompting.
        """
        
        # Best Practice: Structured system prompt with clear instructions
        system_prompt = """You are a cognitive load assessment expert specializing in SQL learning.

Your task is to assess whether a user needs an explanation for a given query based on:
1. User's SQL expertise level (1-5 scale)
2. Query complexity
3. Cognitive Load Theory principles

OUTPUT FORMAT (JSON):
{
  "intrinsic_load": float (1-10),
  "explanation_needed": boolean,
  "explanation_type": "none" | "basic" | "intermediate" | "advanced",
  "reasoning": "brief explanation",
  "complexity_factors": {
    "data_dimensions": float (1-10),
    "analytical_complexity": float (1-10),
    "presentation_complexity": float (1-10)
  }
}

DECISION RULES:
- Explanation needed if: intrinsic_load > (user_expertise * 2)
- Basic explanation: user_expertise <= 2
- Intermediate explanation: user_expertise == 3
- Advanced explanation: user_expertise >= 4
- No explanation: intrinsic_load <= (user_expertise * 2)"""

        # Best Practice: Structured user message
        user_message = f"""Assess this query for a user with SQL expertise level {user_profile.sql_expertise_level}/5:

Query: "{user_query}"

User Profile:
- SQL Expertise: {user_profile.sql_expertise_level}/5
- Cognitive Capacity: {user_profile.cognitive_load_capacity}/5
- Experience with concepts: {json.dumps(user_profile.sql_concept_levels)}

Provide assessment in JSON format."""

        try:
            # Best Practice: Optimized API call with proper parameters
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,  # Reduced for faster response
                temperature=0,    # Deterministic for assessments
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )
            
            # Extract and parse response
            content = response.content[0].text if response.content else "{}"
            
            # Clean JSON response
            content = content.strip()
            if content.startswith('```'):
                content = re.sub(r'```json?\s*', '', content)
                content = re.sub(r'```\s*', '', content)
            
            try:
                assessment_data = json.loads(content)
                
                # Build CognitiveAssessment from response
                intrinsic_load = float(assessment_data.get("intrinsic_load", 5.0))
                
                complexity_factors = assessment_data.get("complexity_factors", {})
                complexity_breakdown = {
                    "data_dimensionality": complexity_factors.get("data_dimensions", intrinsic_load * 0.3),
                    "analytical_complexity": complexity_factors.get("analytical_complexity", intrinsic_load * 0.4),
                    "presentation_complexity": complexity_factors.get("presentation_complexity", intrinsic_load * 0.2),
                    "temporal_pressure": intrinsic_load * 0.1,
                    "intrinsic_load": intrinsic_load,
                    "cft_misfit_penalty": 0.0,
                    "final_complexity_score": intrinsic_load
                }
                
                return CognitiveAssessment(
                    intrinsic_load=intrinsic_load,
                    task_sql_concept="data_analysis",
                    explanation_needed=assessment_data.get("explanation_needed", False),
                    explanation_type=assessment_data.get("explanation_type", "none"),
                    reasoning=assessment_data.get("reasoning", ""),
                    task_classification="Data Analysis",
                    complexity_breakdown=complexity_breakdown,
                    user_capability_threshold=user_profile.sql_expertise_level * 2,
                    final_complexity_score=intrinsic_load
                )
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse assessment response: {e}")
                return self._fallback_assessment(user_query, user_profile)
                
        except Exception as e:
            logger.error(f"Error in complexity assessment: {e}")
            return self._fallback_assessment(user_query, user_profile)
    
    def _fallback_assessment(self, user_query: str, user_profile: UserProfile) -> CognitiveAssessment:
        """Fallback assessment using heuristics."""
        # Simple keyword-based complexity scoring
        query_lower = user_query.lower()
        
        complexity_score = 3.0  # Base score
        
        # Adjust based on keywords
        if any(word in query_lower for word in ['show', 'list', 'display', 'get']):
            complexity_score = 2.0
        elif any(word in query_lower for word in ['analyze', 'compare', 'trend']):
            complexity_score = 5.0
        elif any(word in query_lower for word in ['forecast', 'predict', 'model']):
            complexity_score = 8.0
        
        # Determine if explanation needed
        user_threshold = user_profile.sql_expertise_level * 2
        explanation_needed = complexity_score > user_threshold
        
        if explanation_needed:
            if user_profile.sql_expertise_level <= 2:
                explanation_type = "basic"
            elif user_profile.sql_expertise_level == 3:
                explanation_type = "intermediate"
            else:
                explanation_type = "advanced"
        else:
            explanation_type = "none"
        
        return CognitiveAssessment(
            intrinsic_load=complexity_score,
            task_sql_concept="general",
            explanation_needed=explanation_needed,
            explanation_type=explanation_type,
            reasoning="Fallback heuristic assessment",
            task_classification="Data Analysis",
            complexity_breakdown={
                "data_dimensionality": complexity_score * 0.3,
                "analytical_complexity": complexity_score * 0.4,
                "presentation_complexity": complexity_score * 0.2,
                "temporal_pressure": complexity_score * 0.1,
                "intrinsic_load": complexity_score,
                "cft_misfit_penalty": 0.0,
                "final_complexity_score": complexity_score
            },
            user_capability_threshold=user_threshold,
            final_complexity_score=complexity_score
        )
    
    def generate_optimized_explanation(self, user_query: str, sql_query: str, 
                                      assessment: CognitiveAssessment, 
                                      user_profile: UserProfile) -> ExplanationContent:
        """
        Generate explanation using Anthropic best practices with structured output.
        """
        
        if not assessment.explanation_needed:
            return ExplanationContent(
                explanation_text="",
                chain_of_thought="",
                sql_concepts=[],
                learning_objectives=[],
                complexity_level="none",
                estimated_cognitive_load=1
            )
        
        # Best Practice: Role-specific system prompt
        system_prompt = """You are an expert SQL educator creating personalized explanations.

Your explanations should:
1. Match the user's expertise level
2. Use clear, accessible language
3. Include practical examples
4. Focus on understanding, not memorization
5. Build on existing knowledge

OUTPUT STRUCTURE:
Create a response with these sections clearly marked:

EXPLANATION:
[Main explanation with proper paragraphs and formatting]

KEY_CONCEPTS:
[Comma-separated list of SQL concepts covered]

LEARNING_POINTS:
[Comma-separated list of what the user will learn]

PRACTICE_TIP:
[One actionable tip for improvement]"""

        # Build contextual user message
        expertise_descriptor = {
            1: "complete beginner",
            2: "novice",
            3: "intermediate",
            4: "advanced",
            5: "expert"
        }.get(user_profile.sql_expertise_level, "intermediate")
        
        user_message = f"""Create a {assessment.explanation_type} explanation for a {expertise_descriptor} user.

Original Question: {user_query}

SQL Query to Explain:
```sql
{sql_query}
```

Focus Areas:
- Break down the query step-by-step
- Explain WHY each part is used
- Connect to the business question
- Use analogies if helpful for beginners

Remember: The user has SQL expertise level {user_profile.sql_expertise_level}/5."""

        try:
            # Optimized API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.3,  # Slight creativity for explanations
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )
            
            content = response.content[0].text if response.content else ""
            
            # Extract structured sections
            explanation = self._extract_section_safe(content, "EXPLANATION:", "KEY_CONCEPTS:")
            concepts = self._extract_list_safe(content, "KEY_CONCEPTS:", "LEARNING_POINTS:")
            learning = self._extract_list_safe(content, "LEARNING_POINTS:", "PRACTICE_TIP:")
            
            # Format explanation for readability
            formatted_explanation = self._format_explanation_enhanced(explanation, assessment.explanation_type)
            
            return ExplanationContent(
                explanation_text=formatted_explanation,
                chain_of_thought=f"Generated {assessment.explanation_type} explanation for {expertise_descriptor}",
                sql_concepts=concepts,
                learning_objectives=learning,
                complexity_level=assessment.explanation_type,
                estimated_cognitive_load=int(assessment.intrinsic_load)
            )
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return ExplanationContent(
                explanation_text="I encountered an issue generating the explanation. The query has been executed successfully.",
                chain_of_thought="Error in explanation generation",
                sql_concepts=[],
                learning_objectives=[],
                complexity_level="error",
                estimated_cognitive_load=1
            )
    
    def _extract_section_safe(self, content: str, start: str, end: str) -> str:
        """Safely extract section from content."""
        try:
            if start not in content:
                return ""
            
            start_idx = content.index(start) + len(start)
            
            if end and end in content[start_idx:]:
                end_idx = content.index(end, start_idx)
                return content[start_idx:end_idx].strip()
            
            return content[start_idx:].strip()
        except:
            return ""
    
    def _extract_list_safe(self, content: str, start: str, end: str) -> List[str]:
        """Safely extract comma-separated list."""
        section = self._extract_section_safe(content, start, end)
        if not section:
            return []
        
        items = [item.strip() for item in section.split(',')]
        return [item for item in items if item and len(item) < 100]  # Filter invalid items
    
    def _format_explanation_enhanced(self, text: str, explanation_type: str) -> str:
        """Enhanced formatting for better readability."""
        if not text:
            return ""
        
        # Clean up the text
        text = text.strip()
        text = re.sub(r'\\n', '\n', text)
        text = re.sub(r'\\t', '    ', text)
        
        # Add type-specific formatting
        if explanation_type == "basic":
            # Add emoji indicators for beginners
            text = re.sub(r'^(\d+\.)', r'**Step \1**', text, flags=re.MULTILINE)
            text = text.replace('Note:', '💡 **Note:**')
            text = text.replace('Important:', '⚠️ **Important:**')
            text = text.replace('Example:', '📝 **Example:**')
        
        elif explanation_type == "intermediate":
            # Professional formatting
            text = re.sub(r'^(\d+\.)', r'**\1**', text, flags=re.MULTILINE)
        
        # Ensure proper spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def execute_query(self, user_id: str, user_query: str, 
                     presentation_context: Optional[Dict[str, Any]] = None,
                     include_debug_info: bool = False) -> Union[
                         Tuple[QueryResult, Optional[ExplanationContent]], 
                         Tuple[QueryResult, Optional[ExplanationContent], CognitiveAssessment, UserProfile]
                     ]:
        """
        Execute query with optimized cognitive assessment and explanation generation.
        """
        logger.info(f"Processing query for user {user_id}: {user_query}")
        
        try:
            # Get or create user profile
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = self._create_default_user_profile(user_id)
            
            user_profile = self.user_profiles[user_id]
            
            # Execute query using ReAct Agent
            react_result = self.react_agent.execute_query(user_query)
            
            # Assess cognitive load using optimized method
            cognitive_assessment = self._assess_task_complexity_optimized(user_query, user_profile)
            
            # Generate explanation if needed
            explanation_content = None
            if cognitive_assessment.explanation_needed and react_result.success:
                explanation_content = self.generate_optimized_explanation(
                    user_query=user_query,
                    sql_query=react_result.sql_query,
                    assessment=cognitive_assessment,
                    user_profile=user_profile
                )
                logger.info(f"Generated {cognitive_assessment.explanation_type} explanation")
            
            # Update user profile based on interaction
            self._update_user_profile_optimized(user_id, user_query, cognitive_assessment)
            
            if include_debug_info:
                return react_result, explanation_content, cognitive_assessment, user_profile
            else:
                return react_result, explanation_content
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            
            error_result = QueryResult(
                success=False,
                data=None,
                sql_query="",
                error_message=str(e),
                execution_time=0.0,
                complexity_score=1
            )
            
            if include_debug_info:
                return error_result, None, self._fallback_assessment("", user_profile), user_profile
            else:
                return error_result, None
    
    def _create_default_user_profile(self, user_id: str) -> UserProfile:
        """Create default user profile."""
        return UserProfile(
            user_id=user_id,
            sql_expertise_level=2,
            cognitive_load_capacity=3,
            sql_concept_levels={concept: 1 for concept in self.sql_concepts.keys()},
            prior_query_history=[],
            learning_preferences={"style": "step_by_step"},
            last_updated=datetime.now().isoformat(),
            sql_expertise=2,
            age=25,
            gender="Not specified",
            profession="Student",
            education_level="Bachelor"
        )
    
    def _update_user_profile_optimized(self, user_id: str, user_query: str, 
                                      assessment: CognitiveAssessment):
        """Update user profile based on interaction."""
        if user_id not in self.user_profiles:
            return
        
        profile = self.user_profiles[user_id]
        
        # Add to query history (keep last 20)
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": user_query[:100],  # Truncate for storage
            "complexity": assessment.intrinsic_load,
            "explanation_given": assessment.explanation_needed
        }
        
        profile.prior_query_history.append(interaction)
        profile.prior_query_history = profile.prior_query_history[-20:]
        
        # Update last modified
        profile.last_updated = datetime.now().isoformat()
        
        # Save profiles periodically (every 5 interactions)
        if len(profile.prior_query_history) % 5 == 0:
            self._save_user_profiles()
    
    def process_react_output(self, user_id: str, react_result: QueryResult, 
                            presentation_context: Optional[Dict[str, Any]] = None) -> CognitiveAssessment:
        """Process ReAct output with cognitive assessment."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_default_user_profile(user_id)
        
        user_profile = self.user_profiles[user_id]
        
        # Use optimized assessment
        if react_result.success:
            # Analyze SQL complexity
            sql_concept = self._classify_sql_task(react_result.sql_query)
            complexity = react_result.complexity_score * 2  # Scale to 1-10
            
            return CognitiveAssessment(
                intrinsic_load=complexity,
                task_sql_concept=sql_concept,
                explanation_needed=complexity > (user_profile.sql_expertise_level * 2),
                explanation_type=self._determine_explanation_type(user_profile, complexity),
                reasoning="Automated assessment based on query complexity",
                task_classification="Data Analysis",
                complexity_breakdown={
                    "data_dimensionality": complexity * 0.3,
                    "analytical_complexity": complexity * 0.4,
                    "presentation_complexity": complexity * 0.2,
                    "temporal_pressure": complexity * 0.1,
                    "intrinsic_load": complexity,
                    "cft_misfit_penalty": 0.0,
                    "final_complexity_score": complexity
                },
                user_capability_threshold=user_profile.sql_expertise_level * 2,
                final_complexity_score=complexity
            )
        else:
            # Error case
            return self._fallback_assessment("", user_profile)
    
    def _determine_explanation_type(self, user_profile: UserProfile, complexity: float) -> str:
        """Determine appropriate explanation type."""
        if complexity <= user_profile.sql_expertise_level * 2:
            return "none"
        elif user_profile.sql_expertise_level <= 2:
            return "basic"
        elif user_profile.sql_expertise_level == 3:
            return "intermediate"
        else:
            return "advanced"
    
    def generate_explanation(self, user_query: str, sql_query: str, 
                           assessment: CognitiveAssessment, 
                           user_profile: UserProfile) -> ExplanationContent:
        """Generate explanation (wrapper for backward compatibility)."""
        return self.generate_optimized_explanation(user_query, sql_query, assessment, user_profile)


# Example usage
if __name__ == "__main__":
    try:
        # Initialize agent
        agent = CLTCFTAgent()
        print("✅ CLT-CFT Agent initialized with Anthropic best practices")
        
        # Test query
        test_user = "test_user"
        test_query = "Show me the total sales by product category"
        
        print(f"\n📊 Testing query: {test_query}")
        result, explanation = agent.execute_query(test_user, test_query)
        
        if result.success:
            print(f"✅ Query executed successfully")
            print(f"   Rows returned: {len(result.data) if result.data is not None else 0}")
            print(f"   Execution time: {result.execution_time:.2f}s")
            
            if explanation:
                print(f"\n📚 Explanation provided:")
                print(f"   Type: {explanation.complexity_level}")
                print(f"   Concepts: {', '.join(explanation.sql_concepts)}")
        else:
            print(f"❌ Query failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()