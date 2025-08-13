import streamlit as st
from typing import Optional
import logging
import sys
from pathlib import Path

# Robust import function
def robust_import_modules():
    """Import required modules with multiple fallback strategies."""
    
    # Strategy 1: Try absolute imports (local development)
    try:
        from new_data_assistant_project.src.database.models import User
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        print("✅ Welcome Page: Absolute imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    # Strategy 2: Try direct imports (Docker/production - new structure)
    try:
        from src.database.models import User
        from src.utils.auth_manager import AuthManager
        print("✅ Welcome Page: Direct imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    # Strategy 3: Try relative imports (fallback)
    try:
        from src.database.models import User
        from src.utils.auth_manager import AuthManager
        print("✅ Welcome Page: Relative imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.models import User
        from utils.auth_manager import AuthManager
        print("✅ Welcome Page: Manual path imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
User, AuthManager = robust_import_modules()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_welcome_page(user: User):
    """Render the welcome page with study context and navigation."""
    st.title("🌍 GlobalMart 2026 Market Entry Study")
    st.markdown("""
    Welcome to the research study on intelligent explainable data assistance.
    Your mission is to analyze business data and help evaluate the assistant's capabilities.
    """)
    
    st.markdown("### 🧠 Research Context")
    st.markdown("""
    - We are evaluating how well the system predicts when users need explanations
    - Your feedback helps us assess explanation quality and necessity
    - The study has three phases: Assessment, Task, and Feedback
    """)
    
    st.markdown("### ✅ Consent")
    consent_given = st.checkbox("I consent to participate in this study and for my data to be used anonymously.")
    
    st.markdown("### 🛠️ Technical Requirements")
    st.markdown("""
    - Modern web browser (Chrome, Firefox, Safari)
    - Stable internet connection
    - Approximately 30 minutes of uninterrupted time
    - A quiet environment for focused work
    """)
    
    # Ready to start
    st.markdown("### 🚀 Ready to Begin")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Start Assessment Phase", type="primary", disabled=not consent_given):
            st.session_state.current_page = "assessment"
            st.rerun()
    
    with col2:
        if st.button("💼 Skip to Task Phase", disabled=not consent_given):
            st.session_state.current_page = "task"
            st.rerun()
    
    st.info("💡 **Tip:** You can complete the assessment at any time to get personalized explanations.")
    
    # Study progress indicator
    if user.has_completed_assessment:
        st.markdown("### 📊 Assessment Complete")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Assessment", "✅ Complete")
            st.metric("Level", user.user_level_category)
        
        with col2:
            st.metric("Total Score", f"{user.total_assessment_score}/20")
        
        st.markdown("**Next:** Task Phase (20 minutes)")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Welcome", disabled=True):
            st.session_state.current_page = "welcome"
            st.rerun()
    
    with col2:
        if st.button("📊 Assessment", disabled=not user.has_completed_assessment):
            st.session_state.current_page = "assessment"
            st.rerun()
    
    with col3:
        if st.button("🧪 Task Phase", disabled=not user.has_completed_assessment):
            st.session_state.current_page = "task"
            st.rerun()
    
    with col4:
        if st.button("📝 Feedback", disabled=not user.has_completed_assessment or not st.session_state.get('tasks_completed', False)):
            st.session_state.current_page = "feedback"
            st.rerun() 