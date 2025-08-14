import streamlit as st
from typing import Optional, Dict, Tuple
import logging
from datetime import datetime

# Docker-compatible imports
try:
    from new_data_assistant_project.src.database.models import User
    from new_data_assistant_project.src.utils.path_utils import get_absolute_path
except ImportError:
    from src.database.models import User
    from src.utils.path_utils import get_absolute_path

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self):
        self.db_path = get_absolute_path('src/database/superstore.db')
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'show_registration' not in st.session_state:
            st.session_state.show_registration = False

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user."""
        return st.session_state.get('user', None)
    
    def is_admin(self) -> bool:
        """Check if current user is admin."""
        user = self.get_current_user()
        return user and user.role == 'admin'
    
    def logout(self):
        """Logout current user and clear all user-specific data."""
        # Clear authentication state
        st.session_state.authenticated = False
        st.session_state.user = None
        
        # Clear all user-specific chat histories
        keys_to_remove = [key for key in st.session_state.keys() 
                         if key.startswith('chat_history_user_')]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Clear current user tracking
        if 'current_user_id' in st.session_state:
            st.session_state.current_user_id = None
        
        # Clear pending feedback
        if 'pending_feedback' in st.session_state:
            st.session_state.pending_feedback = {}
        
        st.rerun()
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user.
        Returns: (success: bool, message: str)
        """
        try:
            user = User.authenticate(self.db_path, username, password)
            
            if user:
                user.update_login(self.db_path)
                st.session_state.authenticated = True
                st.session_state.user = user
                logger.info(f"User {username} logged in successfully")
                return True, "Login successful"
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return False, "Invalid username or password"
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, "An error occurred during login"
    
    def register(self, username: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Register new user.
        Returns: (success: bool, message: str)
        """
        try:
            # Validation
            if not username or not password:
                return False, "Username and password are required"
            
            if password != confirm_password:
                return False, "Passwords do not match"
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters long"
            
            # Check if user already exists
            if User.get_by_username(self.db_path, username):
                return False, "Username already exists"
            
            # Create new user
            user = User.create_user(username, password)
            user.save(self.db_path)
            
            logger.info(f"New user registered: {username}")
            
            # Automatically log in the user after successful registration
            login_success, login_message = self.login(username, password)
            if login_success:
                # Set current page to welcome after successful registration and login
                st.session_state.current_page = "welcome"
                st.rerun()
                return True, "Registration successful! Redirecting to welcome page..."
            else:
                return False, f"Registration successful but login failed: {login_message}"
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "An error occurred during registration"
    
    def render_login_page(self):
        """Render login/registration page."""
        st.title("🔐 Intelligent explainable Data Assistant")
        st.markdown("### Welcome to the Intelligent explainable Data Assistant")
        
        if not st.session_state.show_registration:
            self._render_login_form()
        else:
            self._render_registration_form()
    
    def _render_login_form(self):
        """Render login form."""
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                success, message = self.login(username, password)
                if success:
                    st.success(message)
                    # Set current page to welcome after successful login
                    st.session_state.current_page = "welcome"
                    st.rerun()
                else:
                    st.error(message)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Register New Account"):
                st.session_state.show_registration = True
                st.rerun()
    
    def _render_registration_form(self):
        """Render registration form."""
        st.subheader("Register New Account")
        
        with st.form("registration_form"):
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Register")
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if submit:
                success, message = self.register(username, password, confirm_password)
                if success:
                    st.success(message)
                    st.session_state.show_registration = False
                else:
                    st.error(message)
            
            if cancel:
                st.session_state.show_registration = False
                st.rerun()
    '''
    def render_assessment_page(self) -> bool:
        """
        Render SQL expertise assessment page (now optional).
        Returns: True if assessment completed, False otherwise
        """
        user = self.get_current_user()
        if not user:
            return False
        
        st.title("📊 SQL Expertise Assessment")
        st.markdown("""
        This assessment helps us provide personalized explanations tailored to your knowledge level.
        The data for the assessment is also required for the evaluation.
        """)
        
        # Show current assessment status
        if user.has_completed_assessment:
            st.success("✅ Assessment already completed!")
            st.info(f"Your SQL expertise level: {user.sql_expertise_level}/5")
            
            if st.button("🔄 Retake Assessment"):
                user.has_completed_assessment = False
                user.save(self.db_path)
                st.rerun()
        else:
            with st.form("assessment_form"):
                st.subheader("1. SQL Experience")
                sql_experience = st.selectbox(
                    "How would you rate your SQL experience?",
                    [
                        "1 - Complete beginner (never used SQL)",
                        "2 - Novice (basic SELECT statements)",
                        "3 - Intermediate (JOINs, GROUP BY, subqueries)",
                        "4 - Advanced (window functions, CTEs, optimization)",
                        "5 - Expert (database design, complex analytics)"
                    ]
                )
                
                st.subheader("2. Additional Information")
                background = st.text_area(
                    "Tell us about your professional background (optional):",
                    placeholder="e.g., Data Analyst, Software Developer, Business Analyst, Student..."
                )
                
                submit_assessment = st.form_submit_button("Complete Assessment")
                
                if submit_assessment:
                    # Extract numeric values
                    sql_level = int(sql_experience.split(' - ')[0])
                    
                    # Complete assessment
                    user.complete_assessment(self.db_path, sql_level)
                    
                    st.success("Assessment completed! You can now access all features.")
                    st.balloons()
                    st.rerun()
        
        return user.has_completed_assessment
    '''
    def render_user_info(self):
        """Render user info in sidebar."""
        user = self.get_current_user()
        if user:
            with st.sidebar:
                # Clean user info
                st.markdown(f"**{user.username}**")
                st.markdown(f"<span style='color: #666; font-size: 0.9em;'>{user.role.title()}</span>", unsafe_allow_html=True)
                
                # Clean logout button
                st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
                if st.button("Logout", type="secondary", use_container_width=True):
                    self.logout() 