import streamlit as st
from typing import Optional, Dict, Tuple
import logging
from datetime import datetime

# Import PostgreSQL models and config
from postgres_models import User
from postgres_config import PostgresConfig

logger = logging.getLogger(__name__)

class PostgresAuthManager:
    """Manages user authentication and session state using PostgreSQL."""
    
    def __init__(self):
        # Initialize PostgreSQL configuration
        self.postgres_config = PostgresConfig()
        self.db_config = self.postgres_config.get_connection_params()
        
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
        Authenticate user using PostgreSQL.
        Returns: (success: bool, message: str)
        """
        try:
            user = User.authenticate(self.db_config, username, password)
            
            if user:
                user.update_login(self.db_config)
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
        Register new user using PostgreSQL.
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
            if User.get_by_username(self.db_config, username):
                return False, "Username already exists"
            
            # Create new user
            user = User.create_user(username, password)
            user.save(self.db_config)
            
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

    def test_connection(self) -> bool:
        """Test PostgreSQL connection."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            conn.close()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False
