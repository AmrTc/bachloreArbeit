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

@dataclass
class CognitiveAssessment:
    """Simplified cognitive assessment - only intrinsic load vs capacity"""
    intrinsic_load: int       # 1-5 scale (task complexity)
    task_sql_concept: str     # Which SQL concept this task belongs to
    explanation_needed: bool
    explanation_type: str     # "basic", "intermediate", "advanced", "none"
    reasoning: str

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
    
    def __init__(self, user_profiles_path: str = "user_profiles.json", database_path: str = "src/database/superstore.db"):
        """
        Initialize CLT & CFT Agent with Claude Sonnet 4 API and ReAct Agent.
        
        Args:
            user_profiles_path: Path to store user profiles
            database_path: Path to SQLite database for ReAct Agent
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
        
        # Initialize ReAct Agent for SQL query execution
        try:
            self.react_agent = ReActAgent(database_path=database_path)
            logger.info("Successfully initialized ReAct Agent")
        except Exception as e:
            logger.error(f"Failed to initialize ReAct Agent: {e}")
            raise
        
        # Load existing user profiles
        self._load_user_profiles()
        

        

        
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
        
        # Use complexity score from ReAct Agent
        intrinsic_load = react_result.complexity_score
        
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
            reasoning=reasoning
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
        if task_complexity > user_sql_expertise:
            explanation_needed = True
            if user_sql_expertise <= 2:
                explanation_type = "basic"
            elif user_sql_expertise == 3:
                explanation_type = "intermediate"
            else:
                explanation_type = "advanced"
            reasoning = f"Fallback: Task complexity ({task_complexity}) > User expertise ({user_sql_expertise})"
        else:
            explanation_needed = False
            explanation_type = "none"
            reasoning = f"Fallback: User can handle task complexity ({task_complexity}) with expertise level ({user_sql_expertise})"
        
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
                reasoning=f"Query execution failed: {react_result.error_message}"
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
            # Step 1: Execute query using ReAct Agent
            react_result = self.react_agent.execute_query(user_query)
            
            # Step 2: Simplified cognitive assessment
            cognitive_assessment = self.process_react_output(user_id, react_result, presentation_context)
            
            # Step 3: Modify QueryResult based on cognitive load (simplified)
            modified_result = self._modify_query_result_simple(react_result, cognitive_assessment, user_id)
            
            # Step 4: Generate explanation if needed
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
            
            # Step 5: Log interaction
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
                error_message=f"Error executing query: {str(e)}",
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
                    reasoning=f"Query execution failed: {str(e)}"
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
            if cognitive_assessment.intrinsic_load > user_profile.cognitive_load_capacity:
                max_rows = min(5, len(react_result.data))  # High load = fewer rows
                modified_result.data = react_result.data.head(max_rows)
                logger.info(f"Limited results to {max_rows} rows due to cognitive overload")
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
                    sql_expertise_level=csv_data['sql_expertise_level'],
                    cognitive_load_capacity=cognitive_capacity,
                    sql_concept_levels={
                        "basic_select": min(csv_data['sql_expertise_level'], 3),
                        "aggregation": max(1, csv_data['sql_expertise_level'] - 1),
                        "joins": max(1, csv_data['sql_expertise_level'] - 2),
                        "advanced_logic": max(1, csv_data['sql_expertise_level'] - 3),
                        "window_functions": max(1, csv_data['sql_expertise_level'] - 4),
                        "advanced_analytics": max(1, csv_data['sql_expertise_level'] - 4)
                    },
                    prior_query_history=[],
                    learning_preferences={"explanation_style": "step_by_step"},
                    last_updated=datetime.now().isoformat()
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
            last_updated=datetime.now().isoformat()
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

User Context:
- Task SQL Concept: {assessment.task_sql_concept}
- User Concept Level: {concept_level}/5
- Cognitive Load: {assessment.intrinsic_load}/5
- Cognitive Capacity: {user_profile.cognitive_load_capacity}/5
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
        if assessment.intrinsic_load >= 4 and not assessment.explanation_needed:
            current_level = profile.sql_concept_levels.get(assessment.task_sql_concept, 1)
            profile.sql_concept_levels[assessment.task_sql_concept] = min(5, current_level + 1)
            logger.info(f"Increased {assessment.task_sql_concept} level to {profile.sql_concept_levels[assessment.task_sql_concept]}")
        
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

