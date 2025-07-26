import os
import streamlit as st
import time
from datetime import datetime
import logging
from typing import Tuple, Optional, cast
from new_data_assistant_project.src.utils.secrets_path_utils import SecretsPathUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clear Streamlit cache to avoid issues with imports
st.cache_data.clear()
st.cache_resource.clear()

# Import modules using the installed package (no sys.path manipulation needed)
from new_data_assistant_project.src.utils.path_utils import get_project_root, get_absolute_path, get_relative_path
from new_data_assistant_project.src.utils.user_manager import UserManager
from new_data_assistant_project.src.agents.clt_cft_agent import CLTCFTAgent, QueryResult, ExplanationContent

# Konfiguration der Seite
st.set_page_config(
    page_title="Data Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Default paths relative to project root
DEFAULT_DB_PATH = "src/database/superstore.db"

# Initialisierung der Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_manager" not in st.session_state:
    st.session_state.user_manager = UserManager()  # Removed csv_path parameter to use default

def display_chat_message(message, is_user=True):
    """Zeigt eine Chat-Nachricht an"""
    with st.chat_message("user" if is_user else "assistant"):
        st.markdown(message)

def bot_response(user_input):
    """Verarbeitet die Benutzeranfrage mit CLT/CFT Agent"""
    try:
        # Clear cache to ensure latest version is loaded
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Initialize CLT/CFT Agent
        agent = CLTCFTAgent(database_path=get_absolute_path(DEFAULT_DB_PATH))
        
        # Get current user ID from session
        user_id = st.session_state.username
        
        # Execute query (explicitly set include_debug_info=False to get 2-tuple)
        result = agent.execute_query(user_id, user_input, include_debug_info=False)
        modified_result, explanation_content = cast(Tuple[QueryResult, Optional[ExplanationContent]], result)
        
        # Build response
        response_parts = []
        
        # Add query result
        if modified_result.success and modified_result.data is not None:
            response_parts.append(f"**SQL Query:**\n```sql\n{modified_result.sql_query}\n```")
            response_parts.append(f"**Ergebnis:**\n{modified_result.data.to_markdown()}")
        else:
            response_parts.append(f"**Fehler:** {modified_result.error_message}")
        
        # Add explanation if provided
        if explanation_content:
            response_parts.append("---")
            response_parts.append("**Erklärung:**")
            response_parts.append(explanation_content.explanation_text)
        
        return "\n\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in bot_response: {e}")
        import traceback
        traceback.print_exc()
        return f"**Fehler bei der Verarbeitung:** {str(e)}"

def login_form():
    """Zeigt das Login-Formular an"""
    st.header("🔐 Anmeldung")
    
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Anmelden"):
            if st.session_state.user_manager.authenticate_user(username, password):
                st.session_state.user_manager.update_last_login(username)
                st.session_state.username = username
                st.success("Erfolgreich angemeldet!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Ungültige Anmeldedaten!")
    
    with col2:
        if st.button("Testnutzer erstellen"):
            st.session_state.user_manager.create_test_users()
            st.success("Testnutzer wurden erstellt!")
            st.info("Verfügbare Testnutzer:\n- beginner_user\n- intermediate_user\n- expert_user\n\nPasswort für alle: test123")

def main():
    """Hauptfunktion der Chat-Seite"""
    
    # Überprüfe Anmeldung
    if "username" not in st.session_state:
        login_form()
        return
    
    # Sidebar für Benutzereinstellungen
    with st.sidebar:
        st.title("⚙️ Einstellungen")
        
        # Benutzer-Informationen
        user_profile = st.session_state.user_manager.get_user_profile(st.session_state.username)
        st.header(f"👤 {user_profile['username']}")
        st.write(f"E-Mail: {user_profile['email']}")
        st.write(f"SQL-Expertise: {user_profile['sql_expertise_level']}/5")
        st.write(f"Domain-Wissen: {user_profile['domain_knowledge']}/5")
        
        if st.button("🚪 Abmelden"):
            del st.session_state.username
            st.rerun()
        
        st.divider()
        
        # Chat-Statistiken
        st.subheader("📊 Chat-Statistiken")
        st.metric("Nachrichten", len(st.session_state.messages))
        
        if st.session_state.messages:
            user_msgs = len([m for m in st.session_state.messages if m["is_user"]])
            bot_msgs = len([m for m in st.session_state.messages if not m["is_user"]])
            st.metric("Ihre Nachrichten", user_msgs)
            st.metric("Bot-Antworten", bot_msgs)
        
        if st.button("🗑️ Chat löschen"):
            st.session_state.messages = []
            st.rerun()
    
    # Hauptbereich
    st.title("💬 Data Assistant")
    
    # Chat-Container
    chat_container = st.container(height=400)
    
    with chat_container:
        for message in st.session_state.messages:
            display_chat_message(message["content"], message["is_user"])
    
    # Chat-Eingabe
    with st.container():
        user_input = st.text_input(
            "Ihre Frage:",
            placeholder="Stellen Sie eine Frage zur Datenbank...",
            key="user_input"
        )
        
        if st.button("Senden", type="primary"):
            if user_input.strip():
                st.session_state.messages.append({
                    "content": user_input,
                    "is_user": True,
                    "timestamp": datetime.now()
                })
                bot_reply = bot_response(user_input)
                st.session_state.messages.append({
                    "content": bot_reply,
                    "is_user": False,
                    "timestamp": datetime.now()
                })
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        💬 Data Assistant | Entwickelt für Ihre Datenanalyse
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()