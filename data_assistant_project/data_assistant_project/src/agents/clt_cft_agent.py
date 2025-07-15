import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from anthropic import Anthropic
import logging
from datetime import datetime
import re
import os
import sys
from pathlib import Path

# Add project root to Python path for imports when running as script
if __name__ == "__main__":
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    sys.path.append(str(project_root))
    from src.utils.my_config import MyConfig
else:
    from ..utils.my_config import MyConfig  # Relativer Import für Package-Nutzung

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User cognitive profile based on CLT and CFT assessments"""
    user_id: str
    sql_expertise_level: int  # 1-5 scale (novice to expert)
    domain_knowledge: int     # 1-5 scale (business domain understanding)
    cognitive_load_capacity: int  # 1-5 scale (working memory capacity)
    prior_query_history: List[Dict]
    learning_preferences: Dict[str, Any]
    last_updated: str

@dataclass
class CognitiveAssessment:
    """Results of cognitive load and fit assessment"""
    intrinsic_load: int       # 1-5 scale (task complexity)
    extraneous_load: int      # 1-5 scale (presentation complexity)
    cognitive_fit_score: int  # 1-5 scale (PR-PST match)
    explanation_needed: bool
    explanation_type: str     # "basic", "intermediate", "advanced", "none"
    confidence_score: float   # 0-1 scale
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
    
    def __init__(self, user_profiles_path: str = "user_profiles.json"):
        """
        Initialize CLT & CFT Agent with Claude Sonnet 4 API.
        
        Args:
            user_profiles_path: Path to store user profiles
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
        
        # Load existing user profiles
        self._load_user_profiles()
        
        # CLT principles and thresholds
        self.clt_thresholds = {
            "working_memory_limit": 4,  # 3-4 items as per narrow limits principle
            "high_element_interactivity": 3,
            "expertise_effect_threshold": 3
        }
        
        # CFT evaluation criteria
        self.cft_criteria = {
            "spatial_tasks": ["visualization", "chart", "graph", "plot"],
            "symbolic_tasks": ["calculation", "aggregate", "sum", "count", "average"],
            "temporal_tasks": ["trend", "time", "period", "date", "month", "year"]
        }
        
        # SQL concept complexity hierarchy
        self.sql_complexity_hierarchy = {
            1: ["SELECT", "FROM", "WHERE", "basic filtering"],
            2: ["GROUP BY", "ORDER BY", "HAVING", "aggregation"],
            3: ["JOIN", "INNER JOIN", "LEFT JOIN", "table relationships"],
            4: ["SUBQUERY", "CASE WHEN", "UNION", "complex logic"],
            5: ["WINDOW FUNCTIONS", "CTE", "advanced analytics", "recursive queries"]
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
    
    def _assess_intrinsic_cognitive_load(self, query_complexity: int, sql_query: str, user_profile: UserProfile) -> int:
        """
        Assess intrinsic cognitive load based on CLT principles.
        
        Args:
            query_complexity: Complexity score from ReAct Agent (1-5)
            sql_query: The SQL query to analyze
            user_profile: User's cognitive profile
            
        Returns:
            Intrinsic load score (1-5)
        """
        # Base intrinsic load from query complexity
        base_load = query_complexity
        
        # Adjust based on user expertise (expertise reversal effect)
        expertise_adjustment = max(0, 3 - user_profile.sql_expertise_level)
        
        # Element interactivity assessment
        sql_upper = sql_query.upper()
        interactive_elements = 0
        
        # Count simultaneous elements that must be processed
        if 'JOIN' in sql_upper:
            interactive_elements += sql_upper.count('JOIN') * 2  # Each join adds multiple elements
        if 'GROUP BY' in sql_upper and 'HAVING' in sql_upper:
            interactive_elements += 2  # Grouping and filtering interaction
        if 'SUBQUERY' in sql_upper or '(' in sql_query:
            interactive_elements += 3  # Nested structure complexity
        
        # Apply narrow limits principle (3-4 items limit)
        if interactive_elements > self.clt_thresholds["working_memory_limit"]:
            element_load = min(2, interactive_elements - self.clt_thresholds["working_memory_limit"])
        else:
            element_load = 0
        
        intrinsic_load = min(5, base_load + expertise_adjustment + element_load)
        return max(1, intrinsic_load)
    
    def _assess_extraneous_cognitive_load(self, presentation_context: Dict[str, Any]) -> int:
        """
        Assess extraneous cognitive load based on information presentation.
        
        Args:
            presentation_context: Context about how information is presented
            
        Returns:
            Extraneous load score (1-5)
        """
        extraneous_load = 1
        
        # Check for split-attention effects
        if presentation_context.get("multiple_interfaces", False):
            extraneous_load += 1
        
        # Check for redundancy effects
        if presentation_context.get("redundant_information", False):
            extraneous_load += 1
        
        # Check for modality effects
        if presentation_context.get("poor_visual_design", False):
            extraneous_load += 1
        
        return min(5, extraneous_load)
    
    def _assess_cognitive_fit(self, user_query: str, sql_query: str, user_profile: UserProfile) -> Tuple[int, str]:
        """
        Assess cognitive fit between problem representation and problem-solving task (CFT).
        
        Args:
            user_query: Original natural language query
            sql_query: Generated SQL query
            user_profile: User's cognitive profile
            
        Returns:
            Tuple of (fit_score, reasoning)
        """
        query_lower = user_query.lower()
        sql_upper = sql_query.upper()
        
        # Determine task type from user query
        spatial_indicators = sum(1 for term in self.cft_criteria["spatial_tasks"] if term in query_lower)
        symbolic_indicators = sum(1 for term in self.cft_criteria["symbolic_tasks"] if term in query_lower)
        temporal_indicators = sum(1 for term in self.cft_criteria["temporal_tasks"] if term in query_lower)
        
        # Determine dominant task type
        task_indicators = {
            "spatial": spatial_indicators,
            "symbolic": symbolic_indicators,
            "temporal": temporal_indicators
        }
        
        # Find task type with maximum indicators
        max_indicators = max(task_indicators.values())
        dominant_tasks = [task for task, count in task_indicators.items() if count == max_indicators]
        dominant_task = dominant_tasks[0] if dominant_tasks else "unknown"
        
        # Assess fit between task type and SQL representation
        fit_score = 3  # Default neutral fit
        reasoning = f"Task type: {dominant_task}. "
        
        # CFT-based fit assessment
        if dominant_task == "spatial" and any(keyword in sql_upper for keyword in ["ORDER BY", "GROUP BY"]):
            fit_score += 1
            reasoning += "Good fit: spatial task with ordered/grouped data representation. "
        elif dominant_task == "symbolic" and any(keyword in sql_upper for keyword in ["SUM", "COUNT", "AVG", "MAX", "MIN"]):
            fit_score += 1
            reasoning += "Good fit: symbolic task with aggregate operations. "
        elif dominant_task == "temporal" and any(keyword in sql_upper for keyword in ["DATE", "YEAR", "MONTH", "TIME"]):
            fit_score += 1
            reasoning += "Good fit: temporal task with time-based operations. "
        
        # Adjust based on user's domain knowledge
        if user_profile.domain_knowledge >= 4:
            fit_score += 1
            reasoning += "Enhanced fit due to strong domain knowledge. "
        elif user_profile.domain_knowledge <= 2:
            fit_score -= 1
            reasoning += "Reduced fit due to limited domain knowledge. "
        
        # Mental representation reconstruction check
        if user_profile.sql_expertise_level < 3 and fit_score < 3:
            reasoning += "Mental representation reconstruction likely needed. "
        
        return min(5, max(1, fit_score)), reasoning
    
    def _determine_explanation_need(self, assessment: CognitiveAssessment, user_profile: UserProfile) -> Tuple[bool, str, float]:
        """
        Intelligent explanation decision based on CLT & CFT assessment.
        
        Args:
            assessment: Cognitive assessment results
            user_profile: User's cognitive profile
            
        Returns:
            Tuple of (explanation_needed, explanation_type, confidence)
        """
        # Calculate total cognitive load
        total_load = assessment.intrinsic_load + assessment.extraneous_load
        
        # Decision logic based on CLT & CFT principles
        explanation_needed = False
        explanation_type = "none"
        confidence = 0.5
        
        # High intrinsic load threshold
        if assessment.intrinsic_load >= 4:
            explanation_needed = True
            explanation_type = "detailed"
            confidence += 0.3
        
        # Poor cognitive fit
        if assessment.cognitive_fit_score <= 2:
            explanation_needed = True
            if explanation_type == "none":
                explanation_type = "conceptual"
            confidence += 0.2
        
        # User expertise consideration (expertise reversal effect)
        if user_profile.sql_expertise_level <= 2:
            explanation_needed = True
            explanation_type = "basic" if explanation_type == "none" else explanation_type
            confidence += 0.3
        elif user_profile.sql_expertise_level >= 4 and assessment.intrinsic_load <= 2:
            explanation_needed = False
            explanation_type = "none"
            confidence += 0.2
        
        # Working memory overload check
        if total_load > user_profile.cognitive_load_capacity:
            explanation_needed = True
            explanation_type = "simplified"
            confidence += 0.2
        
        confidence = min(1.0, confidence)
        
        return explanation_needed, explanation_type, confidence
    
    def assess_user_cognitive_state(self, user_id: str, user_query: str, sql_query: str, 
                                  query_complexity: int, presentation_context: Optional[Dict[str, Any]] = None) -> CognitiveAssessment:
        """
        Main method to assess user's cognitive state and explanation needs.
        
        Args:
            user_id: Unique user identifier
            user_query: Original natural language query
            sql_query: Generated SQL query
            query_complexity: Complexity score from ReAct Agent
            presentation_context: Context about information presentation
            
        Returns:
            CognitiveAssessment with explanation decision
        """
        # Get or create user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_default_user_profile(user_id)
        
        user_profile = self.user_profiles[user_id]
        
        if presentation_context is None:
            presentation_context = {}
        
        # Assess intrinsic cognitive load (CLT)
        intrinsic_load = self._assess_intrinsic_cognitive_load(query_complexity, sql_query, user_profile)
        
        # Assess extraneous cognitive load (CLT)
        extraneous_load = self._assess_extraneous_cognitive_load(presentation_context)
        
        # Assess cognitive fit (CFT)
        cognitive_fit_score, fit_reasoning = self._assess_cognitive_fit(user_query, sql_query, user_profile)
        
        # Create preliminary assessment
        assessment = CognitiveAssessment(
            intrinsic_load=intrinsic_load,
            extraneous_load=extraneous_load,
            cognitive_fit_score=cognitive_fit_score,
            explanation_needed=False,  # Will be determined next
            explanation_type="none",
            confidence_score=0.0,
            reasoning=fit_reasoning
        )
        
        # Determine explanation need
        explanation_needed, explanation_type, confidence = self._determine_explanation_need(assessment, user_profile)
        
        # Update assessment with decision
        assessment.explanation_needed = explanation_needed
        assessment.explanation_type = explanation_type
        assessment.confidence_score = confidence
        assessment.reasoning += f"Explanation decision: {explanation_type} (confidence: {confidence:.2f})"
        
        # Update user profile with this interaction
        self._update_user_profile(user_id, user_query, sql_query, assessment)
        
        logger.info(f"Cognitive assessment for {user_id}: explanation_needed={explanation_needed}, type={explanation_type}")
        
        return assessment
    
    def generate_explanation(self, user_query: str, sql_query: str, assessment: CognitiveAssessment, 
                           user_profile: UserProfile) -> ExplanationContent:
        """
        Generate personalized explanation using Chain-of-Thought reasoning.
        
        Args:
            user_query: Original natural language query
            sql_query: Generated SQL query
            assessment: Cognitive assessment results
            user_profile: User's cognitive profile
            
        Returns:
            ExplanationContent with tailored explanation
        """
        if not assessment.explanation_needed:
            return ExplanationContent(
                explanation_text="No explanation needed based on your expertise level.",
                chain_of_thought="",
                sql_concepts=[],
                learning_objectives=[],
                complexity_level="none",
                estimated_cognitive_load=1
            )
        
        # Prepare context for Claude
        explanation_level = self._map_explanation_type_to_level(assessment.explanation_type)
        user_expertise = user_profile.sql_expertise_level
        
        system_prompt = f"""You are an intelligent SQL tutor using Chain-of-Thought reasoning to provide personalized explanations.

User Context:
- SQL Expertise Level: {user_expertise}/5
- Explanation Type Needed: {assessment.explanation_type}
- Cognitive Load Capacity: {user_profile.cognitive_load_capacity}/5
- Domain Knowledge: {user_profile.domain_knowledge}/5

Cognitive Load Theory Guidelines:
- Keep explanations within working memory limits (3-4 concepts at once)
- Adjust complexity based on user expertise (expertise reversal effect)
- Reduce extraneous cognitive load through clear presentation

Cognitive Fit Theory Guidelines:
- Match explanation format to the user's mental model
- Help bridge gaps between problem representation and solution approach

Generate a Chain-of-Thought explanation that:
1. Breaks down the SQL query step by step
2. Explains WHY each part is needed for the original question
3. Connects SQL concepts to business logic
4. Adapts complexity to user's expertise level
5. Identifies key learning objectives

Format your response as:
CHAIN_OF_THOUGHT:
[Your step-by-step reasoning process]

EXPLANATION:
[The actual explanation for the user]

SQL_CONCEPTS:
[List of SQL concepts covered, separated by commas]

LEARNING_OBJECTIVES:
[What the user should learn from this explanation, separated by commas]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"""
Original Question: {user_query}

SQL Query to Explain:
{sql_query}

Cognitive Assessment:
- Intrinsic Load: {assessment.intrinsic_load}/5
- Cognitive Fit Score: {assessment.cognitive_fit_score}/5
- Explanation Type: {assessment.explanation_type}

Please provide a personalized explanation following the Chain-of-Thought approach.
"""
                }]
            )
            
            # Extract content safely
            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            
            # Parse the response
            chain_of_thought = self._extract_section(content, "CHAIN_OF_THOUGHT:")
            explanation = self._extract_section(content, "EXPLANATION:")
            sql_concepts = self._extract_list(content, "SQL_CONCEPTS:")
            learning_objectives = self._extract_list(content, "LEARNING_OBJECTIVES:")
            
            return ExplanationContent(
                explanation_text=explanation,
                chain_of_thought=chain_of_thought,
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
            
            # Find next header or end of content
            next_headers = ["CHAIN_OF_THOUGHT:", "EXPLANATION:", "SQL_CONCEPTS:", "LEARNING_OBJECTIVES:"]
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
        return [item for item in items if item]
    
    def _map_explanation_type_to_level(self, explanation_type: str) -> int:
        """Map explanation type to complexity level."""
        mapping = {
            "basic": 1,
            "conceptual": 2,
            "intermediate": 3,
            "detailed": 4,
            "simplified": 2,
            "none": 0
        }
        return mapping.get(explanation_type, 2)
    
    def _create_default_user_profile(self, user_id: str) -> UserProfile:
        """Create a default user profile for new users."""
        return UserProfile(
            user_id=user_id,
            sql_expertise_level=2,  # Assume beginner-intermediate
            domain_knowledge=2,     # Assume basic domain knowledge
            cognitive_load_capacity=3,  # Average working memory capacity
            prior_query_history=[],
            learning_preferences={"explanation_style": "step_by_step"},
            last_updated=datetime.now().isoformat()
        )
    
    def _update_user_profile(self, user_id: str, user_query: str, sql_query: str, assessment: CognitiveAssessment):
        """Update user profile based on interaction."""
        profile = self.user_profiles[user_id]
        
        # Add to query history
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "sql_complexity": assessment.intrinsic_load,
            "explanation_provided": assessment.explanation_needed,
            "explanation_type": assessment.explanation_type
        }
        
        profile.prior_query_history.append(interaction)
        
        # Keep only last 10 interactions
        profile.prior_query_history = profile.prior_query_history[-10:]
        
        # Update expertise estimation based on query complexity handling
        if assessment.intrinsic_load >= 4 and assessment.cognitive_fit_score >= 4:
            # Convert float to int for expertise level
            new_level = min(5, int(profile.sql_expertise_level + 1))
            profile.sql_expertise_level = new_level
        
        profile.last_updated = datetime.now().isoformat()
        
        # Save updated profiles
        self._save_user_profiles()
    
    def evaluate_explanation_effectiveness(self, user_id: str, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate explanation effectiveness for F1-score calculation.
        
        Args:
            user_id: User identifier
            user_feedback: User feedback including whether explanation was needed/helpful
            
        Returns:
            Dictionary with effectiveness metrics
        """
        # This method supports the research evaluation (F1-score calculation)
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
        print(f"API Key value: {api_key}")
        
        # Initialize CLT & CFT Agent
        clt_cft_agent = CLTCFTAgent()
        print("\nCLT & CFT Agent Initialization:")
        print("Agent initialized successfully")
        
        # Example assessment
        user_id = "test_user_1"
        user_query = "What are the top 5 products by sales in each region?"
        sql_query = """SELECT region, product_name, SUM(sales) as total_sales,
                       ROW_NUMBER() OVER (PARTITION BY region ORDER BY SUM(sales) DESC) as rank
                       FROM superstore 
                       GROUP BY region, product_name 
                       HAVING rank <= 5"""
        query_complexity = 4  # From ReAct Agent
        
        # Perform cognitive assessment
        assessment = clt_cft_agent.assess_user_cognitive_state(
            user_id=user_id,
            user_query=user_query,
            sql_query=sql_query,
            query_complexity=query_complexity
        )
        
        print(f"\nAssessment Results:")
        print(f"- Explanation needed: {assessment.explanation_needed}")
        print(f"- Explanation type: {assessment.explanation_type}")
        print(f"- Confidence: {assessment.confidence_score:.2f}")
        print(f"- Intrinsic load: {assessment.intrinsic_load}")
        print(f"- Cognitive fit: {assessment.cognitive_fit_score}")
        
        # Generate explanation if needed
        if assessment.explanation_needed:
            user_profile = clt_cft_agent.user_profiles[user_id]
            explanation = clt_cft_agent.generate_explanation(
                user_query, sql_query, assessment, user_profile
            )
            print(f"\nGenerated Explanation:")
            print(f"Type: {explanation.complexity_level}")
            print(f"Content: {explanation.explanation_text[:200]}...")
            print(f"Concepts covered: {explanation.sql_concepts}")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

