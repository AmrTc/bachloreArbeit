import streamlit as st
from typing import Optional, Dict, Any, List
import logging
import pandas as pd
from datetime import datetime

# Robust import function
def robust_import_modules():
    """Import required modules with multiple fallback strategies."""
    
    # Strategy 1: Try absolute imports (local development)
    try:
        from new_data_assistant_project.src.database.models import User, ChatSession, ExplanationFeedback
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        from new_data_assistant_project.src.utils.chat_manager import ChatManager
        from new_data_assistant_project.src.utils.path_utils import get_absolute_path
        print("✅ Task Page: Absolute imports successful")
        return User, AuthManager, ChatManager, get_absolute_path
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    # Strategy 2: Try direct imports (Docker/production - new structure)
    try:
        from src.database.models import User, ChatSession, ExplanationFeedback
        from src.utils.auth_manager import AuthManager
        from src.utils.chat_manager import ChatManager
        from src.utils.path_utils import get_absolute_path
        print("✅ Task Page: Direct imports successful")
        return User, AuthManager, ChatManager, get_absolute_path
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    # Strategy 3: Try relative imports (fallback)
    try:
        from src.database.models import User, ChatSession, ExplanationFeedback
        from src.utils.auth_manager import AuthManager
        from src.utils.chat_manager import ChatManager
        from src.utils.path_utils import get_absolute_path
        print("✅ Task Page: Relative imports successful")
        return User, AuthManager, ChatManager, get_absolute_path
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        import sys
        from pathlib import Path
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.models import User, ChatSession, ExplanationFeedback
        from utils.auth_manager import AuthManager
        from utils.chat_manager import ChatManager
        from utils.path_utils import get_absolute_path
        print("✅ Task Page: Manual path imports successful")
        return User, AuthManager, ChatManager, get_absolute_path
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
User, AuthManager, ChatManager, get_absolute_path = robust_import_modules()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionAccuracyTracker:
    """Tracks prediction accuracy for explanation decisions in PostgreSQL."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_accuracy (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER,
                    user_id INTEGER,
                    predicted_explanation_needed BOOLEAN,
                    actual_explanation_needed BOOLEAN,
                    confidence_score NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error ensuring prediction_accuracy table: {e}")
    
    def record_prediction(
        self,
        session_id: int,
        user_id: int,
        predicted_explanation_needed: bool,
        actual_explanation_needed: bool,
        confidence_score: float = None,
    ):
        """Record a prediction and its actual outcome in PostgreSQL."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO prediction_accuracy (
                    session_id, user_id, predicted_explanation_needed,
                    actual_explanation_needed, confidence_score
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    user_id,
                    predicted_explanation_needed,
                    actual_explanation_needed,
                    confidence_score,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
    
    def get_accuracy_metrics(self, user_id: int = None) -> Dict[str, Any]:
        """Get accuracy metrics for predictions from PostgreSQL."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    """
                    SELECT predicted_explanation_needed, actual_explanation_needed, confidence_score
                    FROM prediction_accuracy WHERE user_id = %s
                    """,
                    (user_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT predicted_explanation_needed, actual_explanation_needed, confidence_score
                    FROM prediction_accuracy
                    """
                )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if not rows:
                return {
                    "total_predictions": 0,
                    "accuracy": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                }
            total = len(rows)
            correct = sum(1 for row in rows if row[0] == row[1])
            accuracy = correct / total if total > 0 else 0.0
            true_positives = sum(1 for row in rows if row[0] and row[1])
            false_positives = sum(1 for row in rows if row[0] and not row[1])
            false_negatives = sum(1 for row in rows if not row[0] and row[1])
            precision = (
                true_positives / (true_positives + false_positives)
                if (true_positives + false_positives) > 0
                else 0.0
            )
            recall = (
                true_positives / (true_positives + false_negatives)
                if (true_positives + false_negatives) > 0
                else 0.0
            )
            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )
            return {
                "total_predictions": total,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
            }
        except Exception as e:
            logger.error(f"Error getting accuracy metrics: {e}")
            return {
                "total_predictions": 0,
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
            }

def render_task_page(user: User):
    """Render the main task page with research study prompts and prediction accuracy tracking."""
    
    st.markdown("""
    # 💼 Task Phase - GlobalMart 2026 Market Entry Analysis
    
    ## Your Mission: Strategic Data Analysis
    
    You are a business analyst at GlobalMart, a retail chain preparing for a major market entry in 2026.
    After successful US expansion (2014-2017), GlobalMart plans to enter new markets in 2026.
    Your task is to analyze comprehensive retail data to develop strategic insights for our expansion.
    On the left sidebar you will find the tasks you need to complete. You can complete the task in any Order, 
    but you need to complete all tasks. After you have completed all tasks, you can proceed to the feedback phase.

    **Important:**
    If you mark a task as completed, you can't change it.
    
    **Duration:** 20 minutes
    
    ---
    """)
    
    # Initialize managers
    auth_manager = AuthManager()
    chat_manager = ChatManager()
    tracker = PredictionAccuracyTracker(auth_manager.db_config)
    
    # Sidebar with study prompts
    with st.sidebar:
        st.markdown("### 📋 Research Study Tasks")
        
        # Initialize task completion tracking
        if 'completed_tasks' not in st.session_state:
            st.session_state.completed_tasks = set()
        
        # Task prompts for the study (complexity will be determined by CLT-CFT agent)
        study_tasks = [
            {
                "id": 1,
                "title": "Basic Sales Overview",
                "prompt": "What is the total sales amount for each region?"
            },
            {
                "id": 2,
                "title": "Growth Pattern Analysis",
                "prompt": "What growth patterns do you identify in our data? Which product categories and regions show the strongest growth, and what does this mean for 2026?"
            },
            {
                "id": 3,
                "title": "Customer Segmentation Analysis",
                "prompt": "Identify the most profitable customer segments in our existing market. What demographic and behavioral characteristics do our most valuable customers have?"
            },
            {
                "id": 4,
                "title": "Profitability Deep-Dive",
                "prompt": "Analyze profitability across product categories, regions, and customer segments. Where do we make the most money and why? What factors drive our margins?"
            },
            {
                "id": 5,
                "title": "Market Potential Forecasting",
                "prompt": "Based on our historical data, forecast the market potential for 2026. What revenue and profit targets are realistic for market expansion?"
            },
            {
                "id": 6,
                "title": "Strategic Entry Analysis",
                "prompt": "Develop a data-driven market entry strategy for 2026. Which product categories should we prioritize? Which customer segments should we target first? Support your recommendations with data insights."
            },
            {
                "id": 7,
                "title": "Risk Pattern Analysis",
                "prompt": "What risks do you identify based on our historical performance data? Which product categories or strategies have performed poorly in the past and should be avoided?"
            },
            {
                "id": 8,
                "title": "ROI Projection Analysis",
                "prompt": "Calculate the expected Return on Investment for the proposed market entry strategy. Create different scenarios (Best-Case, Base-Case, Worst-Case) with concrete numbers and timelines. What assumptions underlie your calculations?"
            }
        ]
        st.markdown("**Complete these 8 tasks in any order:**")
        
        for task in study_tasks:
            task_key = f"task_{task['id']}"
            is_completed = task['id'] in st.session_state.completed_tasks
            
            if st.button(
                f"{'✅' if is_completed else '📋'} {task['title']}",
                key=f"task_button_{task['id']}",
                help="Click to start this analysis task"
            ):
                st.session_state.current_task = task
                st.rerun()
        
        st.markdown("---")
        
        # Progress tracking
        completed_count = len(st.session_state.completed_tasks)
        total_tasks = len(study_tasks)
        progress = completed_count / total_tasks if total_tasks > 0 else 0
        
        st.markdown(f"### 📊 Progress: {completed_count}/{total_tasks} tasks completed")
        st.progress(progress)
        
        if completed_count == total_tasks:
            st.session_state.tasks_completed = True
            st.success("🎉 All tasks completed! Please proceed to the feedback phase.")
            if st.button("Continue to Feedback"):
                st.session_state.current_page = "feedback"
                st.rerun()
        #Will be deleted
        '''
        st.markdown("---")
        
        # Prediction accuracy metrics
        st.markdown("### 🎯 System Performance")
        metrics = tracker.get_accuracy_metrics(user.id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Predictions", metrics['total_predictions'])
            st.metric("Accuracy", f"{metrics['accuracy']:.1%}")
        
        with col2:
            st.metric("Precision", f"{metrics['precision']:.1%}")
            st.metric("Recall", f"{metrics['recall']:.1%}")
        
        st.markdown(f"**F1 Score**: {metrics['f1_score']:.1%}")
        '''
    # Main chat interface
    #st.markdown("### 💬 Data Analysis Assistant")
    '''
    # Display user profile summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Your Level", user.user_level_category)
    
    with col2:
        st.metric("Total Score", f"{user.total_assessment_score}/20")
    '''
    
    
    # Chat interface
    chat_manager.render_chat_interface(user)
    
    # Enhanced feedback collection for research
    if 'last_session_id' in st.session_state and 'last_explanation_given' in st.session_state:
        st.markdown("---")
        st.markdown("### 📝 Research Feedback")
        
        session_id = st.session_state.last_session_id
        explanation_given = st.session_state.last_explanation_given
        
        col1, col2 = st.columns(2)
        
        with col1:
            if explanation_given:
                st.markdown("**Explanation was provided**")
                was_helpful = st.radio(
                    "Was the explanation helpful?",
                    ["Yes", "No", "Somewhat"],
                    key=f"helpful_{session_id}"
                )
                
                if st.button("Submit Feedback", key=f"submit_helpful_{session_id}"):
                    # Record feedback
                    feedback = ExplanationFeedback.create_feedback(
                        user_id=user.id,
                        session_id=session_id,
                        explanation_given=True,
                        was_helpful=(was_helpful == "Yes")
                    )
                    feedback.save(auth_manager.db_path)
                    
                    # Record prediction accuracy
                    tracker.record_prediction(
                        session_id=session_id,
                        user_id=user.id,
                        predicted_explanation_needed=True,
                        actual_explanation_needed=(was_helpful in ["Yes", "Somewhat"])
                    )
                    
                    # Mark current task as completed if it exists
                    if 'current_task' in st.session_state:
                        st.session_state.completed_tasks.add(st.session_state.current_task['id'])
                        del st.session_state.current_task
                    
                    st.success("✅ Feedback recorded!")
                    del st.session_state.last_session_id
                    del st.session_state.last_explanation_given
                    st.rerun()
            
            else:
                st.markdown("**No explanation was provided**")
                would_have_been_needed = st.radio(
                    "Would an explanation have been helpful?",
                    ["Yes", "No", "Maybe"],
                    key=f"needed_{session_id}"
                )
                
                if st.button("Submit Feedback", key=f"submit_needed_{session_id}"):
                    # Record feedback
                    feedback = ExplanationFeedback.create_feedback(
                        user_id=user.id,
                        session_id=session_id,
                        explanation_given=False,
                        would_have_been_needed=(would_have_been_needed == "Yes")
                    )
                    feedback.save(auth_manager.db_path)
                    
                    # Record prediction accuracy
                    tracker.record_prediction(
                        session_id=session_id,
                        user_id=user.id,
                        predicted_explanation_needed=False,
                        actual_explanation_needed=(would_have_been_needed == "Yes")
                    )
                    
                    # Mark current task as completed if it exists
                    if 'current_task' in st.session_state:
                        st.session_state.completed_tasks.add(st.session_state.current_task['id'])
                        del st.session_state.current_task
                    
                    st.success("✅ Feedback recorded!")
                    del st.session_state.last_session_id
                    del st.session_state.last_explanation_given
                    st.rerun()
        
        st.markdown("**It is necessary fo the survey to answer the following questions**")
        st.markdown("""
        - **Yes**: The explanation was helpful or would have been helpful
        - **No**: The explanation wasn't helpful or wasn't needed
        - **Somewhat/Maybe**: Partial usefulness or uncertainty
        """)
    # Current task display with example query and completion
    if 'current_task' in st.session_state:
        task = st.session_state.current_task
        
        # Task header
        st.markdown(f"### 📋 **Current Task:** {task['title']}")
        st.markdown(f"copy this **Prompt:** {task['prompt']}")
        '''
        # Example query box with copy functionality
        st.markdown("---")
        st.markdown("### 💡 **Example Query**")
        
        # Create a copyable text box
        example_query = task['prompt']
        
        # Create a styled text box that looks like it can be copied
        st.markdown(f"""
        <div style="
            background-color: #f0f2f6; 
            border: 1px solid #ccc; 
            border-radius: 5px; 
            padding: 15px; 
            font-family: monospace; 
            font-size: 14px;
            color: #333;
            margin: 10px 0;
        ">
            {example_query}
        </div>
        """, unsafe_allow_html=True)
        
        # Copy button
        if st.button("📋 Copy Query", key=f"copy_{task['id']}"):
            st.write("Query copied to clipboard!")
            # Note: Streamlit doesn't have native clipboard support, but this gives user feedback
        '''
        # Task completion section
        st.markdown("---")
        st.markdown("### ✅ **Task Completion**")
        
        st.markdown("**Instructions:**")
        st.markdown("""
        1. Copy the example query above
        2. Paste it into the chat interface below
        3. Review the results
        4. Click 'Mark as Completed' when done
        """)
        
        if st.button("🎯 Mark as Completed", key=f"complete_{task['id']}", type="primary"):
            # Mark task as completed
            st.session_state.completed_tasks.add(task['id'])
            del st.session_state.current_task
            st.success(f"✅ Task '{task['title']}' completed!")
            st.rerun()
        
        #st.markdown("---")

    # Navigation
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Welcome"):
            st.session_state.current_page = "welcome"
            st.rerun()
    
    with col2:
        if st.button("Assessment"):
            st.session_state.current_page = "assessment"
            st.rerun()
    
    with col3:
        if st.button("Task Phase"):
            st.session_state.current_page = "task"
            st.rerun()
    
    with col4:
        if st.button("Feedback", disabled=not st.session_state.get('tasks_completed', False)):
            st.session_state.current_page = "feedback"
            st.rerun() 