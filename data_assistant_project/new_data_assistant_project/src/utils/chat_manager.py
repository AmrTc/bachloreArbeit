import streamlit as st
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

# Docker-compatible imports
try:
    from new_data_assistant_project.src.database.models import ChatSession, ExplanationFeedback, User
    from new_data_assistant_project.src.agents.clt_cft_agent import CLTCFTAgent
    from new_data_assistant_project.src.utils.path_utils import get_absolute_path
except ImportError:
    from src.database.models import ChatSession, ExplanationFeedback, User
    from src.agents.clt_cft_agent import CLTCFTAgent
    from src.utils.path_utils import get_absolute_path

logger = logging.getLogger(__name__)

class ChatManager:
    """Manages isolated chat sessions for users with feedback collection."""
    
    def __init__(self):
        self.db_path = get_absolute_path('src/database/superstore.db')
        self.agent = CLTCFTAgent(database_path=self.db_path)
        
        # Initialize global session state for feedback tracking
        if 'pending_feedback' not in st.session_state:
            st.session_state.pending_feedback = {}
        if 'current_user_id' not in st.session_state:
            st.session_state.current_user_id = None
    
    def _get_user_chat_key(self, user_id: int) -> str:
        """Get session state key for user's chat history."""
        return f'chat_history_user_{user_id}'
    
    def _get_user_chat_history(self, user_id: int) -> list:
        """Get chat history for specific user from session state."""
        chat_key = self._get_user_chat_key(user_id)
        return st.session_state.get(chat_key, [])
    
    def _set_user_chat_history(self, user_id: int, chat_history: list):
        """Set chat history for specific user in session state."""
        chat_key = self._get_user_chat_key(user_id)
        st.session_state[chat_key] = chat_history
    
    def _clear_user_chat_history(self, user_id: int):
        """Clear chat history for specific user."""
        chat_key = self._get_user_chat_key(user_id)
        st.session_state[chat_key] = []
    
    def load_user_chat_history(self, user_id: int, limit: int = 20):
        """Load recent chat history for user from database."""
        try:
            # Check if we're switching users - if so, clear session state
            if st.session_state.current_user_id != user_id:
                # Clear all user chat histories from session state when switching users
                keys_to_remove = [key for key in st.session_state.keys() if key.startswith('chat_history_user_')]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.session_state.current_user_id = user_id
            
            # Check if chat history is already loaded for this user
            existing_history = self._get_user_chat_history(user_id)
            if existing_history:
                return  # Already loaded
            
            # Load from database
            sessions = ChatSession.get_user_sessions(self.db_path, user_id, limit)
            
            chat_history = []
            for session in sessions:
                chat_history.append({
                    'session_id': session.id,
                    'user_message': session.user_message,
                    'system_response': session.system_response,
                    'explanation_given': session.explanation_given,
                    'timestamp': session.created_at
                })
            
            # Reverse to show oldest first and store in user-specific session state
            self._set_user_chat_history(user_id, list(reversed(chat_history)))
            
        except Exception as e:
            logger.error(f"Error loading chat history for user {user_id}: {e}")
            self._set_user_chat_history(user_id, [])
    
    def process_user_message(self, user: User, user_message: str) -> Tuple[str, bool, Optional[int]]:
        """
        Process user message and return response.
        Returns: (response_text, explanation_given, session_id)
        """
        try:
            # Execute query using CLT-CFT agent
            result = self.agent.execute_query(user.username, user_message, include_debug_info=False)
            modified_result, explanation_content = result
            
            # Build response
            response_parts = []
            explanation_given = False
            
            if modified_result.success and modified_result.data is not None:
                response_parts.append(f"**SQL Query:**")
                response_parts.append(f"```sql\n{modified_result.sql_query}\n```")
                response_parts.append(f"**Results:** {len(modified_result.data)} rows retrieved")
                
                # Display data in a nice format
                if len(modified_result.data) > 0:
                    import pandas as pd
                    df = pd.DataFrame(modified_result.data)
                    response_parts.append("**Data:**")
                    response_parts.append(df.to_markdown(index=False))
            else:
                response_parts.append("❌ **Error:** Unable to process your query.")
                if modified_result.error:
                    response_parts.append(f"Details: {modified_result.error}")
            
            # Add explanation if provided
            if explanation_content and explanation_content.explanation_text:
                response_parts.append("---")
                response_parts.append("**💡 Explanation:**")
                response_parts.append(explanation_content.explanation_text)
                explanation_given = True
            
            response_text = '\n\n'.join(response_parts)
            
            # Save chat session to database
            chat_session = ChatSession.create_session(
                user_id=user.id,
                user_message=user_message,
                system_response=response_text,
                sql_query=modified_result.sql_query if modified_result.success else None,
                explanation_given=explanation_given
            )
            chat_session.save(self.db_path)
            
            # Add to user-specific session state
            current_history = self._get_user_chat_history(user.id)
            current_history.append({
                'session_id': chat_session.id,
                'user_message': user_message,
                'system_response': response_text,
                'explanation_given': explanation_given,
                'timestamp': datetime.now()
            })
            self._set_user_chat_history(user.id, current_history)
            
            return response_text, explanation_given, chat_session.id
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = f"❌ **System Error:** {str(e)}"
            
            # Still save error session
            try:
                chat_session = ChatSession.create_session(
                    user_id=user.id,
                    user_message=user_message,
                    system_response=error_response,
                    explanation_given=False
                )
                chat_session.save(self.db_path)
                return error_response, False, chat_session.id
            except:
                return error_response, False, None
    
    def render_feedback_form(self, session_id: int, explanation_given: bool, user_id: int):
        """Render feedback form for a specific session."""
        feedback_key = f"feedback_{session_id}"
        
        if feedback_key not in st.session_state.pending_feedback:
            st.session_state.pending_feedback[feedback_key] = {
                'shown': False,
                'submitted': False
            }
        
        feedback_state = st.session_state.pending_feedback[feedback_key]
        
        if not feedback_state['submitted']:
            st.markdown("---")
            st.markdown("**📝 Feedback:** Help us improve the system!")
            
            with st.form(f"feedback_form_{session_id}"):
                if explanation_given:
                    was_needed = st.radio(
                        "Was this explanation necessary for you?",
                        ["Yes", "No"],
                        key=f"needed_{session_id}"
                    )
                    
                    was_helpful = None
                    if was_needed == "Yes":
                        was_helpful = st.radio(
                            "Was the explanation helpful?",
                            ["Yes", "No"],
                            key=f"helpful_{session_id}"
                        )
                    
                    submit_feedback = st.form_submit_button("Submit Feedback")
                    
                    if submit_feedback:
                        # Save feedback
                        feedback = ExplanationFeedback.create_feedback(
                            user_id=user_id,
                            session_id=session_id,
                            explanation_given=True,
                            was_needed=was_needed == "Yes",
                            was_helpful=was_helpful == "Yes" if was_helpful else None
                        )
                        feedback.save(self.db_path)
                        
                        feedback_state['submitted'] = True
                        st.success("Thank you for your feedback!")
                        st.rerun()
                
                else:
                    would_have_been_needed = st.radio(
                        "Would an explanation have been helpful for this query?",
                        ["Yes", "No"],
                        key=f"would_need_{session_id}"
                    )
                    
                    submit_feedback = st.form_submit_button("Submit Feedback")
                    
                    if submit_feedback:
                        # Save feedback
                        feedback = ExplanationFeedback.create_feedback(
                            user_id=user_id,
                            session_id=session_id,
                            explanation_given=False,
                            would_have_been_needed=would_have_been_needed == "Yes"
                        )
                        feedback.save(self.db_path)
                        
                        feedback_state['submitted'] = True
                        st.success("Thank you for your feedback!")
                        st.rerun()
    
    def render_chat_interface(self, user: User):
        """Render the main chat interface."""
        st.title("🤖 Intelligent Data Assistant")
        st.markdown(f"Welcome back, **{user.name or user.username}**! Ask me anything about your data.")
        
        # Load chat history for this specific user
        self.load_user_chat_history(user.id)
        
        # Get user-specific chat history
        user_chat_history = self._get_user_chat_history(user.id)
        
        # Display chat history
        if user_chat_history:
            st.markdown("### 📜 Chat History")
            
            for i, chat in enumerate(user_chat_history):
                # User message
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("**🧑‍💻**")
                    with col2:
                        st.markdown(f"**You:** {chat['user_message']}")
                
                # System response
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("**🤖**")
                    with col2:
                        st.markdown(chat['system_response'])
                
                # Feedback form for recent messages (last 3)
                if i >= len(user_chat_history) - 3 and chat.get('session_id'):
                    self.render_feedback_form(
                        chat['session_id'], 
                        chat['explanation_given'], 
                        user.id
                    )
                
                st.markdown("---")
        
        # New message input
        st.markdown("### 💬 Ask a Question")
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Type your question about the data:",
                placeholder="e.g., 'Show me the top 5 sales by region' or 'What are the trends in customer orders?'",
                height=100
            )
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                send_message = st.form_submit_button("📤 Send Message", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("🗑️ Clear Chat", use_container_width=True)
            
            if send_message and user_input.strip():
                with st.spinner("Processing your request..."):
                    response, explanation_given, session_id = self.process_user_message(user, user_input.strip())
                    st.rerun()
            
            if clear_chat:
                self._clear_user_chat_history(user.id)
                # Clear only feedback for this user's sessions
                user_feedback_keys = [key for key in st.session_state.pending_feedback.keys() 
                                    if key.startswith(f"feedback_")]
                for key in user_feedback_keys:
                    del st.session_state.pending_feedback[key]
                st.success("Chat history cleared!")
                st.rerun()
        
        # Usage tips
        with st.expander("💡 Usage Tips"):
            st.markdown("""
            **Example Questions:**
            - "Show me total sales by region"
            - "What are the top 10 products by profit?"
            - "Compare sales between different customer segments"
            - "Find all orders with discounts greater than 20%"
            - "What's the average order value by category?"
            
            **Features:**
            - 🧠 Intelligent explanations based on your expertise level
            - 📊 Automatic data visualization
            - 💡 Step-by-step SQL breakdown
            - 📚 Learning-focused guidance
            """) 