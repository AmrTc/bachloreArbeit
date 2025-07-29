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
    
    # Strategy 1: Try global import setup
    try:
        import new_data_assistant_project
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        from new_data_assistant_project.src.utils.chat_manager import ChatManager
        from new_data_assistant_project.src.database.schema import create_tables, create_admin_user
        from new_data_assistant_project.src.utils.path_utils import get_absolute_path
        print("✅ Strategy 1: Global imports successful")
        return True, (AuthManager, ChatManager, create_tables, create_admin_user, get_absolute_path)
    except ImportError as e:
        print(f"❌ Strategy 1 failed: {e}")
    
    # Strategy 2: Try absolute imports with current working directory
    try:
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        from new_data_assistant_project.src.utils.chat_manager import ChatManager
        from new_data_assistant_project.src.database.schema import create_tables, create_admin_user
        from new_data_assistant_project.src.utils.path_utils import get_absolute_path
        print("✅ Strategy 2: Absolute imports successful")
        return True, (AuthManager, ChatManager, create_tables, create_admin_user, get_absolute_path)
    except ImportError as e:
        print(f"❌ Strategy 2 failed: {e}")
    
    # Strategy 3: Try relative imports (Docker fallback)
    try:
        from src.utils.auth_manager import AuthManager
        from src.utils.chat_manager import ChatManager
        from src.database.schema import create_tables, create_admin_user
        from src.utils.path_utils import get_absolute_path
        print("✅ Strategy 3: Relative imports successful")
        return True, (AuthManager, ChatManager, create_tables, create_admin_user, get_absolute_path)
    except ImportError as e:
        print(f"❌ Strategy 3 failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        # Add specific paths
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from utils.auth_manager import AuthManager
        from utils.chat_manager import ChatManager
        from database.schema import create_tables, create_admin_user
        from utils.path_utils import get_absolute_path
        print("✅ Strategy 4: Manual path imports successful")
        return True, (AuthManager, ChatManager, create_tables, create_admin_user, get_absolute_path)
    except ImportError as e:
        print(f"❌ Strategy 4 failed: {e}")
    
    return False, None

# Import required modules
import_success, modules = robust_import()

if not import_success:
    st.error("❌ Critical Error: Could not import required modules. Please check the installation.")
    st.error(f"Current working directory: {os.getcwd()}")
    st.error(f"Python path: {sys.path[:3]}...")
    st.stop()

# Unpack modules
AuthManager, ChatManager, create_tables, create_admin_user, get_absolute_path = modules

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Intelligent Explanation System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on startup
@st.cache_resource
def initialize_system():
    """Initialize database and create admin user if needed."""
    try:
        import os
        import traceback
        
        # Comprehensive diagnostics
        cwd = os.getcwd()
        logger.info(f"🔧 System Initialization Starting...")
        logger.info(f"📁 Current working directory: {cwd}")
        logger.info(f"🐍 Python path includes: {sys.path[:3]}...")
        
        # Check project structure
        required_dirs = ["src", "src/database", "frontend"]
        missing_dirs = []
        
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                logger.info(f"✅ Found directory: {dir_name}")
            else:
                missing_dirs.append(dir_name)
                logger.error(f"❌ Missing directory: {dir_name}")
        
        if missing_dirs:
            logger.error(f"❌ Missing directories: {missing_dirs}")
            logger.error(f"Current directory contents: {os.listdir('.')}")
            return False
        
        # Check database file
        db_path = "src/database/superstore.db"
        if os.path.exists(db_path):
            logger.info(f"✅ Database file exists: {db_path}")
        else:
            logger.warning(f"⚠️ Database file will be created: {db_path}")
            
        # Initialize database
        create_tables()
        create_admin_user()
        
        logger.info("🎯 System initialized successfully!")
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
    
    # Check authentication
    if not auth_manager.is_authenticated():
        auth_manager.render_login_page()
        return
    
    # Get current user
    user = auth_manager.get_current_user()
    
    # Render user info in sidebar
    auth_manager.render_user_info()
    
    # Check if user needs to complete assessment
    if user.role == 'user' and not user.has_completed_assessment:
        completed = auth_manager.render_assessment_page()
        if not completed:
            return
    
    # Role-based navigation and content
    if user.role == 'admin':
        render_admin_interface()
    else:
        render_user_interface(user)

def render_admin_interface():
    """Render admin interface with navigation."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Admin Navigation")
    
    page = st.sidebar.radio(
        "Select Page:",
        ["🤖 Data Assistant", "📊 Evaluation Dashboard"]
    )
    
    if page == "🤖 Data Assistant":
        user = auth_manager.get_current_user()
        chat_manager.render_chat_interface(user)
    else:
        # Import evaluation dashboard with same robust strategy
        try:
            from new_data_assistant_project.frontend.pages.evaluation_dashboard import render_evaluation_dashboard
        except ImportError:
            try:
                from frontend.pages.evaluation_dashboard import render_evaluation_dashboard
            except ImportError:
                from pages.evaluation_dashboard import render_evaluation_dashboard
        
        render_evaluation_dashboard()

def render_user_interface(user):
    """Render user interface (chat only)."""
    chat_manager.render_chat_interface(user)

if __name__ == "__main__":
    main()