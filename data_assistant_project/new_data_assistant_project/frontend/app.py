import os
import sys
from pathlib import Path
import streamlit as st
import logging

# AUTO-NAVIGATE TO CORRECT DIRECTORY & SETUP IMPORTS
def ensure_correct_working_directory():
    """Automatically navigate to the correct working directory and setup imports."""
    current_file = Path(__file__).resolve()
    
    # We expect to be in: .../new_data_assistant_project/frontend/app.py
    # So we need to go up one level to new_data_assistant_project
    expected_project_root = current_file.parent.parent
    
    # Check if we're in the right place
    if expected_project_root.name == 'new_data_assistant_project':
        # Change to the project root directory
        os.chdir(expected_project_root)
        print(f"✅ Auto-navigated to: {expected_project_root}")
    else:
        # Try to find new_data_assistant_project in current or parent directories
        search_path = current_file.parent
        for _ in range(5):  # Search up to 5 levels up
            new_project = search_path / 'new_data_assistant_project'
            if new_project.exists() and (new_project / 'src').exists():
                os.chdir(new_project)
                print(f"✅ Found and navigated to: {new_project}")
                break
            search_path = search_path.parent
            if search_path == search_path.parent:  # Reached filesystem root
                break
        else:
            print(f"❌ Warning: Could not find new_data_assistant_project directory")
            print(f"Current working directory: {os.getcwd()}")
    
    # Setup Python path for imports
    project_root = Path.cwd()
    parent_dir = project_root.parent
    
    # Add paths to sys.path
    paths_to_add = [str(project_root), str(parent_dir)]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Try to import our global setup
    try:
        import new_data_assistant_project
        print("✅ Global import setup loaded successfully")
    except ImportError:
        print("⚠️ Could not load global import setup, using fallback")

# Execute directory navigation before any other imports
ensure_correct_working_directory()

# Robust import function with multiple fallback strategies
def robust_import():
    """Import required modules with multiple fallback strategies."""
    
    try:
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        from new_data_assistant_project.src.utils.chat_manager import ChatManager
        print("✅ Strategy 1: Absolute imports successful")
        return AuthManager, ChatManager
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    try:
        from src.utils.auth_manager import AuthManager
        from src.utils.chat_manager import ChatManager
        print("✅ Strategy 2: Direct imports successful")
        return AuthManager, ChatManager
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    try:
        from src.utils.auth_manager import AuthManager
        from src.utils.chat_manager import ChatManager
        print("✅ Strategy 3: Relative imports successful")
        return AuthManager, ChatManager
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Manual path manipulation as last resort
    current_dir = Path.cwd()
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(current_dir / 'src'))
    try:
        from utils.auth_manager import AuthManager
        from utils.chat_manager import ChatManager
        print("✅ Strategy 4: Manual path imports successful")
        return AuthManager, ChatManager
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
AuthManager, ChatManager = robust_import()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import traceback

def initialize_system():
    """Initialize system by checking PostgreSQL connection and managers."""
    try:
        # Check required directories
        required_dirs = ['src', 'src/database', 'frontend']
        missing_dirs = []
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)
                logger.error(f"❌ Missing directory: {dir_name}")
        
        if missing_dirs:
            logger.error(f"❌ Missing directories: {missing_dirs}")
            logger.error(f"Current directory contents: {os.listdir('.')}")
            return False
        
        # Test PostgreSQL connection
        try:
            auth_manager = AuthManager()
            if auth_manager.test_connection():
                logger.info("✅ PostgreSQL connection successful")
            else:
                logger.error("❌ PostgreSQL connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection test failed: {e}")
            return False
        
        logger.info("🎯 System initialized successfully with PostgreSQL!")
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization error: {e}")
        logger.error(f"📍 Current working directory: {os.getcwd()}")
        logger.error(f"📂 Directory contents: {os.listdir('.')}")
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return False

# Initialize system
system_ready = initialize_system()

if not system_ready:
    st.error("❌ System initialization failed. Please check the logs.")
    st.stop()

# Initialize managers
auth_manager = AuthManager()
chat_manager = ChatManager()

def main():
    """Main application logic with authentication and role-based routing."""
    
    # Initialize session state for current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "welcome"
    
    # Check authentication
    if not auth_manager.is_authenticated():
        auth_manager.render_login_page()
        return
    
    # Get current user
    user = auth_manager.get_current_user()
    
    # Render user info in sidebar
    auth_manager.render_user_info()
    
    # Users go directly to welcome page after registration
    # Assessment is optional and can be accessed via navigation
    
    # Role-based navigation and content
    if user.role == 'admin':
        render_admin_interface()
    else:
        render_user_interface(user)

def render_admin_interface():
    """Render admin interface with navigation."""
    
    # Direct page routing without sidebar navigation
    if st.session_state.current_page == "welcome":
        try:
            from new_data_assistant_project.frontend.pages.welcome_page import render_welcome_page
        except ImportError:
            try:
                from frontend.pages.welcome_page import render_welcome_page
            except ImportError:
                try:
                    from pages.welcome_page import render_welcome_page
                except ImportError:
                    st.error("❌ Could not import welcome page")
                    return
        
        user = auth_manager.get_current_user()
        render_welcome_page(user)
    
    elif st.session_state.current_page == "assessment":
        try:
            from new_data_assistant_project.frontend.pages.assessment_page import render_assessment_page
        except ImportError:
            try:
                from frontend.pages.assessment_page import render_assessment_page
            except ImportError:
                try:
                    from pages.assessment_page import render_assessment_page
                except ImportError:
                    st.error("❌ Could not import assessment page")
                    return
        
        user = auth_manager.get_current_user()
        render_assessment_page(user)
    
    elif st.session_state.current_page == "task":
        try:
            from new_data_assistant_project.frontend.pages.task_page import render_task_page
        except ImportError:
            try:
                from frontend.pages.task_page import render_task_page
            except ImportError:
                try:
                    from pages.task_page import render_task_page
                except ImportError:
                    st.error("❌ Could not import task page")
                    return
        
        user = auth_manager.get_current_user()
        render_task_page(user)
    
    elif st.session_state.current_page == "chat":
        user = auth_manager.get_current_user()
        chat_manager.render_chat_interface(user)
    
    else:  # Evaluation Dashboard
        # Import evaluation dashboard with same robust strategy
        try:
            from new_data_assistant_project.frontend.pages.evaluation_dashboard import render_evaluation_dashboard
        except ImportError:
            try:
                from frontend.pages.evaluation_dashboard import render_evaluation_dashboard
            except ImportError:
                try:
                    from pages.evaluation_dashboard import render_evaluation_dashboard
                except ImportError:
                    st.error("❌ Could not import evaluation dashboard")
                    return
        
        render_evaluation_dashboard()

def render_user_interface(user):
    """Render user interface with 4-page structure."""
    
    # Initialize current page if not set - default to welcome
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "welcome"
    
    # Clean sidebar separator
    st.sidebar.markdown("<div style='margin: 1rem 0; border-top: 1px solid #f0f0f0;'></div>", unsafe_allow_html=True)
    

    
    # Page routing
    if st.session_state.current_page == "welcome":
        try:
            from new_data_assistant_project.frontend.pages.welcome_page import render_welcome_page
        except ImportError:
            try:
                from frontend.pages.welcome_page import render_welcome_page
            except ImportError:
                try:
                    from pages.welcome_page import render_welcome_page
                except ImportError:
                    st.error("❌ Could not import welcome page")
                    return
        
        render_welcome_page(user)
    
    elif st.session_state.current_page == "assessment":
        try:
            from new_data_assistant_project.frontend.pages.assessment_page import render_assessment_page
        except ImportError:
            try:
                from frontend.pages.assessment_page import render_assessment_page
            except ImportError:
                try:
                    from pages.assessment_page import render_assessment_page
                except ImportError:
                    st.error("❌ Could not import assessment page")
                    return
        
        render_assessment_page(user)
    
    elif st.session_state.current_page == "task":
        try:
            from new_data_assistant_project.frontend.pages.task_page import render_task_page
        except ImportError:
            try:
                from frontend.pages.task_page import render_task_page
            except ImportError:
                try:
                    from pages.task_page import render_task_page
                except ImportError:
                    st.error("❌ Could not import task page")
                    return
        
        render_task_page(user)
    
    elif st.session_state.current_page == "data_assistant":
        user = auth_manager.get_current_user()
        chat_manager.render_chat_interface(user)
    
    elif st.session_state.current_page == "feedback":
        # Check if user has completed tasks
        if not st.session_state.get('tasks_completed', False):
            st.error("❌ You must complete all tasks before accessing the feedback page.")
            st.info("Please return to the Task Phase and complete all 8 tasks.")
            st.session_state.current_page = "task"
            st.rerun()
            return
        
        try:
            from new_data_assistant_project.frontend.pages.feedback_page import render_feedback_page
        except ImportError:
            try:
                from frontend.pages.feedback_page import render_feedback_page
            except ImportError:
                try:
                    from pages.feedback_page import render_feedback_page
                except ImportError:
                    st.error("❌ Could not import feedback page")
                    return
        
        render_feedback_page(user)


if __name__ == "__main__":
    main()