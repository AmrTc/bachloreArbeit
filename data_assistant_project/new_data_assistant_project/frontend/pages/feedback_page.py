import streamlit as st
from typing import Optional, Dict, Any
import logging

# Robust import function
def robust_import_modules():
    """Import required modules with multiple fallback strategies."""
    
    # Strategy 1: Try absolute imports (local development)
    try:
        from new_data_assistant_project.src.database.models import User, ExplanationFeedback
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        print("✅ Feedback Page: Absolute imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    # Strategy 2: Try direct imports (Docker/production - new structure)
    try:
        from src.database.models import User, ExplanationFeedback
        from src.utils.auth_manager import AuthManager
        print("✅ Feedback Page: Direct imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    # Strategy 3: Try relative imports (fallback)
    try:
        from src.database.models import User, ExplanationFeedback
        from src.utils.auth_manager import AuthManager
        print("✅ Feedback Page: Relative imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        import sys
        from pathlib import Path
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.models import User, ExplanationFeedback
        from utils.auth_manager import AuthManager
        print("✅ Feedback Page: Manual path imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
User, AuthManager = robust_import_modules()

# Import ComprehensiveFeedback model
try:
    from new_data_assistant_project.src.database.models import ComprehensiveFeedback
    print("✅ ComprehensiveFeedback import successful")
except ImportError:
    try:
        from src.database.models import ComprehensiveFeedback
        print("✅ ComprehensiveFeedback direct import successful")
    except ImportError:
        print("❌ ComprehensiveFeedback import failed")
        ComprehensiveFeedback = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_feedback_page(user: User):
    """Render the feedback page with 7 specific research questions."""
    
    # Check if user has completed tasks
    if not st.session_state.get('tasks_completed', False):
        st.error("❌ You must complete all tasks before accessing the feedback page.")
        st.info("Please return to the Task Phase and complete all 8 tasks.")
        return
    
    st.markdown("""
    # 📝 Study Feedback
    
    ## Thank you for participating in our research study!
    
    Please take a moment to provide feedback about your experience with the intelligent explanation system.
    Your responses will help us improve the system for future users.
    
    **This feedback is completely anonymous and will only be used for research purposes.**
    
    ---
    """)
    
    # Initialize feedback responses
    if 'feedback_responses' not in st.session_state:
        st.session_state.feedback_responses = {}
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Question 1: Explanation frequency
    st.markdown("### 1. Explanation Frequency")
    st.markdown("How would you rate the explanation frequency?")
    st.markdown("*(1 = Too few explanations, 5 = Too many explanations)*")
    
    frequency_rating = st.slider(
        "Explanation frequency rating:",
        min_value=1,
        max_value=5,
        value=st.session_state.feedback_responses.get('frequency_rating', 3),
        key="frequency_rating"
    )
    st.session_state.feedback_responses['frequency_rating'] = frequency_rating
    
    st.markdown("---")
    
    # Question 2: Explanation length
    st.markdown("### 2. Explanation Length")
    st.markdown("How would you rate the explanation length?")
    st.markdown("*(1 = Too short, 5 = Too long)*")
    
    length_rating = st.slider(
        "Explanation length rating:",
        min_value=1,
        max_value=5,
        value=st.session_state.feedback_responses.get('length_rating', 3),
        key="length_rating"
    )
    st.session_state.feedback_responses['length_rating'] = length_rating
    
    st.markdown("---")
    
    # Question 3: Explanation quality
    st.markdown("### 3. Explanation Quality")
    st.markdown("How would you rate the overall explanation quality?")
    st.markdown("*(1 = Poor, 5 = Excellent)*")
    
    quality_rating = st.slider(
        "Explanation quality rating:",
        min_value=1,
        max_value=5,
        value=st.session_state.feedback_responses.get('quality_rating', 3),
        key="quality_rating"
    )
    st.session_state.feedback_responses['quality_rating'] = quality_rating
    
    st.markdown("---")
    
    # Question 4: Manual trigger preference
    st.markdown("### 4. Manual Trigger Preference")
    st.markdown("Would you prefer a system where you can trigger explanations manually?")
    
    manual_trigger = st.radio(
        "Manual trigger preference:",
        ["Yes", "No"],
        index=st.session_state.feedback_responses.get('manual_trigger_index', 1),
        key="manual_trigger"
    )
    st.session_state.feedback_responses['manual_trigger'] = manual_trigger
    st.session_state.feedback_responses['manual_trigger_index'] = ["Yes", "No"].index(manual_trigger)
    
    manual_reason = st.text_area(
        "Why or why not?",
        value=st.session_state.feedback_responses.get('manual_reason', ''),
        key="manual_reason",
        placeholder="Please explain your preference..."
    )
    st.session_state.feedback_responses['manual_reason'] = manual_reason
    
    st.markdown("---")
    
    # Question 5: Automatic explanation preference
    st.markdown("### 5. Automatic Explanation Preference")
    st.markdown("Would you prefer a system that automatically provides explanations?")
    
    auto_explanation = st.radio(
        "Automatic explanation preference:",
        ["Yes", "No"],
        index=st.session_state.feedback_responses.get('auto_explanation_index', 1),
        key="auto_explanation"
    )
    st.session_state.feedback_responses['auto_explanation'] = auto_explanation
    st.session_state.feedback_responses['auto_explanation_index'] = ["Yes", "No"].index(auto_explanation)
    
    auto_reason = st.text_area(
        "Why or why not?",
        value=st.session_state.feedback_responses.get('auto_reason', ''),
        key="auto_reason",
        placeholder="Please explain your preference..."
    )
    st.session_state.feedback_responses['auto_reason'] = auto_reason
    
    st.markdown("---")
    
    # Question 6: System accuracy belief
    st.markdown("### 6. System Accuracy")
    st.markdown("Do you believe that the system's predictions were accurate?")
    
    system_accuracy = st.radio(
        "System accuracy belief:",
        ["Yes", "No", "Somewhat"],
        index=st.session_state.feedback_responses.get('system_accuracy_index', 2),
        key="system_accuracy"
    )
    st.session_state.feedback_responses['system_accuracy'] = system_accuracy
    st.session_state.feedback_responses['system_accuracy_index'] = ["Yes", "No", "Somewhat"].index(system_accuracy)
    
    st.markdown("---")
    
    # Question 7: Recommendation
    st.markdown("### 7. Recommendation")
    st.markdown("Would you recommend the use of an intelligent system for your Sales Department (if you owned a company)?")
    
    recommendation = st.radio(
        "Recommendation:",
        ["Yes", "No", "Maybe"],
        index=st.session_state.feedback_responses.get('recommendation_index', 0),
        key="recommendation"
    )
    st.session_state.feedback_responses['recommendation'] = recommendation
    st.session_state.feedback_responses['recommendation_index'] = ["Yes", "No", "Maybe"].index(recommendation)
    
    st.markdown("---")
    
    # Submit feedback
    if st.button("Submit Feedback", type="primary", key="submit_feedback"):
        try:
            if ComprehensiveFeedback is None:
                st.error("❌ Error: Could not import feedback model. Please try again.")
                return
            
            # Get database path from auth manager
            db_config = auth_manager.db_config
            
            # Create and save comprehensive feedback
            feedback = ComprehensiveFeedback.create_feedback(
                user_id=user.id,
                frequency_rating=st.session_state.feedback_responses.get('frequency_rating', 3),
                frequency_reason=st.session_state.feedback_responses.get('frequency_reason', ''),
                explanation_quality_rating=st.session_state.feedback_responses.get('quality_rating', 3),
                explanation_quality_reason=st.session_state.feedback_responses.get('quality_reason', ''),
                system_helpfulness_rating=st.session_state.feedback_responses.get('helpfulness_rating', 3),
                system_helpfulness_reason=st.session_state.feedback_responses.get('helpfulness_reason', ''),
                learning_improvement_rating=st.session_state.feedback_responses.get('learning_rating', 3),
                learning_improvement_reason=st.session_state.feedback_responses.get('learning_reason', ''),
                auto_explanation=st.session_state.feedback_responses.get('auto_explanation', 'Yes') == 'Yes',
                auto_reason=st.session_state.feedback_responses.get('auto_reason', ''),
                system_accuracy=st.session_state.feedback_responses.get('system_accuracy', 'Somewhat'),
                system_accuracy_index=st.session_state.feedback_responses.get('system_accuracy_index', 2),
                recommendation=st.session_state.feedback_responses.get('recommendation', 'Yes'),
                recommendation_index=st.session_state.feedback_responses.get('recommendation_index', 0)
            )
            
            # Save to PostgreSQL database
            feedback.save(db_config)
            
            st.success("✅ Thank you for your valuable feedback! Your responses have been recorded in our research database.")
            st.session_state.feedback_completed = True
            
            # Show completion message
            st.markdown("""
            ### 🎉 Study Completion
            
            **Thank you for participating in our research study!**
            
            Your feedback will help us improve intelligent explanation systems for data analysis.
            
            **Study Summary:**
            - Assessment Phase: ✅ Complete
            - Task Phase: ✅ Complete  
            - Feedback Phase: ✅ Complete
            
            **Your contribution helps:**
            - Improve AI systems for data analysis
            - Develop better user experiences
            - Advance adaptive learning systems
            
            You may now close this browser window.
            """)
            
        except Exception as e:
            st.error(f"❌ Error saving feedback: {e}")
            logger.error(f"Feedback save error: {e}")
    
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
        if st.button("Feedback", disabled=True):
            st.session_state.current_page = "feedback"
            st.rerun() 