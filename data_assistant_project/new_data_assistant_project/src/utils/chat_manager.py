import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import sys

# PostgreSQL imports
try:
    from new_data_assistant_project.src.database.postgres_models import ChatSession, ExplanationFeedback, User
    from new_data_assistant_project.src.agents.clt_cft_agent import CLTCFTAgent, UserProfile
    from new_data_assistant_project.src.database.postgres_config import PostgresConfig
except ImportError:
    from src.database.postgres_models import ChatSession, ExplanationFeedback, User
    from src.agents.clt_cft_agent import CLTCFTAgent, UserProfile
    from src.database.postgres_config import PostgresConfig

logger = logging.getLogger(__name__)

class ChatManager:
    """Enhanced Chat Manager with full table display and visualization capabilities."""
    
    def __init__(self):
        # Initialize PostgreSQL configuration
        self.postgres_config = PostgresConfig()
        self.db_config = self.postgres_config.get_connection_params()
        self.agent = CLTCFTAgent(database_config=self.db_config, enable_caching=True)
        
        # Initialize session state
        if 'pending_feedback' not in st.session_state:
            st.session_state.pending_feedback = {}
        if 'current_user_id' not in st.session_state:
            st.session_state.current_user_id = None

        if 'auto_visualize' not in st.session_state:
            st.session_state.auto_visualize = True
    
    def _get_user_chat_key(self, user_id: int) -> str:
        """Get session state key for user's chat history."""
        return f'chat_history_user_{user_id}'
    
    def _get_user_chat_history(self, user_id: int) -> list:
        """Get chat history for specific user."""
        chat_key = self._get_user_chat_key(user_id)
        return st.session_state.get(chat_key, [])
    
    def _set_user_chat_history(self, user_id: int, chat_history: list):
        """Set chat history for specific user."""
        chat_key = self._get_user_chat_key(user_id)
        st.session_state[chat_key] = chat_history
    
    def _clear_user_chat_history(self, user_id: int):
        """Clear chat history for specific user."""
        chat_key = self._get_user_chat_key(user_id)
        st.session_state[chat_key] = []
        try:
            ChatSession.delete_user_sessions(self.db_config, user_id)
        except Exception as e:
            logger.error(f"Error clearing database chat history: {e}")
    
    def _create_visualization(self, data: pd.DataFrame, viz_type: str = 'auto') -> None:
        """Create and display visualization based on data."""
        try:
            if data.empty:
                st.warning("No data to visualize")
                return
            
            # Auto-detect best visualization
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
            date_cols = data.select_dtypes(include=['datetime64']).columns.tolist()
            
            if viz_type == 'auto':
                # Time series detection
                if date_cols and numeric_cols:
                    viz_type = 'line'
                # Categorical vs numeric
                elif categorical_cols and numeric_cols:
                    if len(data[categorical_cols[0]].unique()) <= 10:
                        viz_type = 'bar'
                    else:
                        viz_type = 'scatter'
                # Two numeric columns
                elif len(numeric_cols) >= 2:
                    viz_type = 'scatter'
                # Single numeric column with categories
                elif len(numeric_cols) == 1 and categorical_cols:
                    viz_type = 'bar'
                # Pie chart for small categorical data
                elif len(data) <= 10 and numeric_cols:
                    viz_type = 'pie'
                else:
                    st.info("Could not determine best visualization. Showing data table.")
                    return
            
            # Create visualization based on type
            if viz_type == 'bar' and categorical_cols and numeric_cols:
                fig = px.bar(
                    data,
                    x=categorical_cols[0],
                    y=numeric_cols[0],
                    title=f"{numeric_cols[0]} by {categorical_cols[0]}",
                    color=categorical_cols[1] if len(categorical_cols) > 1 else None
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif viz_type == 'line' and (date_cols or numeric_cols):
                x_col = date_cols[0] if date_cols else data.index
                y_col = numeric_cols[0] if numeric_cols else data.columns[0]
                fig = px.line(
                    data,
                    x=x_col,
                    y=y_col,
                    title=f"{y_col} over {x_col if not isinstance(x_col, pd.Index) else 'Index'}",
                    markers=True if len(data) < 50 else False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif viz_type == 'scatter' and len(numeric_cols) >= 2:
                fig = px.scatter(
                    data,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[1]} vs {numeric_cols[0]}",
                    color=categorical_cols[0] if categorical_cols else None,
                    size=numeric_cols[2] if len(numeric_cols) > 2 else None
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif viz_type == 'pie' and categorical_cols and numeric_cols:
                fig = px.pie(
                    data,
                    names=categorical_cols[0],
                    values=numeric_cols[0],
                    title=f"Distribution of {numeric_cols[0]}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif viz_type == 'heatmap' and len(numeric_cols) >= 2:
                corr_matrix = data[numeric_cols].corr()
                fig = px.imshow(
                    corr_matrix,
                    title="Correlation Heatmap",
                    color_continuous_scale='RdBu',
                    aspect='auto'
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info(f"Visualization type '{viz_type}' not implemented or insufficient data.")
                
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            st.error(f"Could not create visualization: {str(e)}")
    
    def _execute_python_code(self, code: str, data: pd.DataFrame) -> Any:
        """Execute Python code safely with data context."""
        try:
            # Create execution context
            exec_globals = {
                'pd': pd,
                'px': px,
                'go': go,
                'data': data,
                'df': data,  # Alias for convenience
                'st': st,
                'plt': None  # Matplotlib if needed
            }
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            # Execute code
            exec(code, exec_globals)
            
            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            # Check if any plotly figures were created
            for key, value in exec_globals.items():
                if isinstance(value, go.Figure):
                    st.plotly_chart(value, use_container_width=True)
                    
            if output:
                st.code(output, language='text')
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            st.error(f"Code execution error: {str(e)}")
            return False
    
    def _get_or_create_user_profile(self, user: User):
        """Get or create user profile for CLT-CFT assessment."""
        try:
            if user.username in self.agent.user_profiles:
                return self.agent.user_profiles[user.username]
            
            level_mapping = {
                "Beginner": 1,
                "Novice": 2,
                "Intermediate": 3,
                "Advanced": 4,
                "Expert": 5
            }
            
            sql_expertise = level_mapping.get(user.user_level_category, 3)
            cognitive_capacity = max(1, min(5, user.total_assessment_score // 4))
            
            profile = UserProfile(
                user_id=user.username,
                sql_expertise_level=sql_expertise,
                cognitive_load_capacity=cognitive_capacity,
                sql_concept_levels=user.sql_concept_levels or {},
                prior_query_history=user.prior_query_history or [],
                learning_preferences=user.learning_preferences or {},
                last_updated=datetime.now().isoformat(),
                sql_expertise=sql_expertise,
                age=user.age or 25,
                gender=user.gender or "Not specified",
                profession=user.profession or "Student",
                education_level=user.education_level or "Bachelor"
            )
            
            self.agent.user_profiles[user.username] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return UserProfile(
                user_id=user.username,
                sql_expertise_level=3,
                cognitive_load_capacity=3,
                sql_concept_levels={},
                prior_query_history=[],
                learning_preferences={},
                last_updated=datetime.now().isoformat(),
                sql_expertise=3,
                age=25,
                gender="Not specified",
                profession="Student",
                education_level="Bachelor"
            )
    
    def process_user_message(self, user: User, user_message: str) -> Tuple[str, bool, Optional[int], Optional[pd.DataFrame]]:
        """
        Process user message with enhanced capabilities.
        Returns: (response_text, explanation_given, session_id, data_frame)
        """
        try:
            # Check if Python code execution is requested
            if user_message.lower().startswith("python:") or user_message.lower().startswith("code:"):
                code_request = user_message[7:] if user_message.lower().startswith("python:") else user_message[5:]
                
                # Get last query result if available
                last_data = st.session_state.get('last_query_data', None)
                if last_data is not None:
                    # Generate Python code
                    code = self.agent.react_agent.generate_python_code(last_data, code_request)
                    st.code(code, language='python')
                    
                    # Execute code
                    self._execute_python_code(code, last_data)
                    return "Python code executed successfully", False, None, last_data
                else:
                    return "No data available. Please run a query first.", False, None, None
            
            # Execute query with cached data analysis
            result = self.agent.execute_query(
                user.username, 
                user_message,
                include_debug_info=False
            )
            modified_result, explanation_content = result
            
            # Check if SQL should be shown (only for explanations)
            show_sql = explanation_content is not None
            
            # Build response
            response_parts = []
            explanation_given = False
            data_frame = None
            
            if modified_result.success and modified_result.data is not None:
                data_frame = modified_result.data
                
                # Store for Python execution
                st.session_state.last_query_data = data_frame
                
                # Only show SQL if explanation is provided
                if show_sql and modified_result.sql_query:
                    response_parts.append("### 📝 SQL Query (for reference)")
                response_parts.append(f"```sql\n{modified_result.sql_query}\n```")
                
                # Data Summary (always show)
                response_parts.append(f"### 📊 Analysis Results")
                response_parts.append(f"- **Rows found:** {len(data_frame)}")
                response_parts.append(f"- **Columns:** {', '.join(data_frame.columns)}")
                response_parts.append(f"- **Analysis time:** {modified_result.execution_time:.2f}s")
                
                # Results description
                response_parts.append("### 📋 Data Results")
                response_parts.append("Here are the results of your data analysis:")
                
            else:
                response_parts.append("### ❌ Analysis Error")
                if modified_result.error_message:
                    response_parts.append(f"**Error:** {modified_result.error_message}")
                response_parts.append("\n**Suggestions:**")
                response_parts.append("- Try rephrasing your question")
                response_parts.append("- Be more specific about what data you want to see")
                response_parts.append("- Ask about available tables or data structure")
            
            # Add explanation if provided
            if explanation_content and explanation_content.explanation_text:
                response_parts.append("### 💡 Explanation")
                response_parts.append(explanation_content.explanation_text)
                explanation_given = True
            
            response_text = '\n\n'.join(response_parts)
            
            # Save chat session
            chat_session = ChatSession.create_session(
                user_id=user.id,
                user_message=user_message,
                system_response=response_text,
                sql_query=modified_result.sql_query if modified_result.success else None,
                explanation_given=explanation_given
            )
            chat_session.save(self.db_config)
            
            # Update chat history
            current_history = self._get_user_chat_history(user.id)
            current_history.append({
                'session_id': chat_session.id,
                'user_message': user_message,
                'system_response': response_text,
                'explanation_given': explanation_given,
                'data': data_frame,
                'timestamp': datetime.now()
            })
            self._set_user_chat_history(user.id, current_history)
            
            return response_text, explanation_given, chat_session.id, data_frame
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            error_response = f"### ❌ System Error\nI encountered an error: {str(e)}\n\nPlease try rephrasing your query."
            
            try:
                chat_session = ChatSession.create_session(
                    user_id=user.id,
                    user_message=user_message,
                    system_response=error_response,
                    explanation_given=False
                )
                chat_session.save(self.db_config)
                return error_response, False, chat_session.id, None
            except:
                return error_response, False, None, None
    
    def render_chat_interface(self, user: User):
        """Render enhanced chat interface with visualization controls."""
        st.title("🤖 Intelligent Data Assistant")
        st.markdown(f"Welcome, **{user.username}**! I can help you analyze data, create visualizations, and execute Python code.")
        
        # Settings in sidebar
        with st.sidebar:
            st.markdown("### ⚙️ Settings")

            st.session_state.auto_visualize = st.checkbox(
                "Auto-create Visualizations",
                value=st.session_state.auto_visualize,
                help="Automatically create charts for query results"
            )
            
            # Quick actions
            st.markdown("### 🚀 Quick Actions")
            if st.button("Show Tables"):
                st.session_state.pending_query = "What tables are available in the database?"
            if st.button("Sample Data"):
                st.session_state.pending_query = "Show me sample data from the first table"
            if st.button("Data Overview"):
                st.session_state.pending_query = "Give me an overview of all available data"
            
            # Show available tables info
            if hasattr(self.agent, 'react_agent') and hasattr(self.agent.react_agent, 'get_available_tables_info'):
                st.markdown("### 📋 Cached Tables")
                try:
                    tables_info = self.agent.react_agent.get_available_tables_info()
                    st.markdown(tables_info)
                except:
                    st.info("Tables information not available")
        
        # Load chat history
        skip_load_history = st.session_state.get(f'skip_load_history_user_{user.id}', False)
        if not skip_load_history:
            self.load_user_chat_history(user.id)
        
        user_chat_history = self._get_user_chat_history(user.id)
        
        # Display chat history
        if user_chat_history:
            st.markdown("### 📜 Chat History")
            
            for i, chat in enumerate(user_chat_history):
                # User message
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("**You:**")
                    with col2:
                        st.markdown(chat['user_message'])
                
                # System response
                with st.container():
                    st.markdown(chat['system_response'])
                    
                    # Display data table if available
                    if chat.get('data') is not None and not chat['data'].empty:
                        with st.expander("📊 View Full Data Table", expanded=True):
                            st.dataframe(
                                chat['data'],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Download button
                            csv = chat['data'].to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"query_result_{i}.csv",
                                mime="text/csv"
                            )
                            
                        # Auto-visualization
                        if st.session_state.auto_visualize:
                            with st.expander("📈 Visualization", expanded=True):
                                viz_type = st.selectbox(
                                    "Chart Type",
                                    ["auto", "bar", "line", "scatter", "pie", "heatmap"],
                                    key=f"viz_type_{i}"
                                )
                                self._create_visualization(chat['data'], viz_type)
                
                # Feedback form for recent messages
                if i >= len(user_chat_history) - 3 and chat.get('session_id'):
                    self.render_feedback_form(
                        chat['session_id'], 
                        chat['explanation_given'], 
                        user.id
                    )
                
                st.markdown("---")
        
        # New message input
        st.markdown("### 💬 Ask About Your Data")
        st.markdown("""
        **How to use:**
        - Ask questions in natural language about your data
        - The system provides direct data results (no SQL code shown)
        - SQL code is only shown when explanations are needed
        - Start with 'python:' for custom Python analysis
        """)
        
        # Check for pending query
        pending_query = st.session_state.get('pending_query', '')
        
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Your data question:",
                value=pending_query,
                placeholder="e.g., 'What are the top selling products?' or 'Show sales trends by month'",
                height=100
            )
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col2:
                send_message = st.form_submit_button("Send", type="primary")
            with col3:
                clear_chat = st.form_submit_button("Clear", type="secondary")
            
            if send_message and user_input.strip():
                st.session_state[f'skip_load_history_user_{user.id}'] = False
                st.session_state.pending_query = ''  # Clear pending query
                with st.spinner("Processing..."):
                    response, explanation_given, session_id, data = self.process_user_message(
                        user, 
                        user_input.strip()
                    )
                    st.rerun()
            
            if clear_chat:
                self._clear_user_chat_history(user.id)
                st.session_state[f'skip_load_history_user_{user.id}'] = True
                st.session_state.pending_query = ''
                st.success("Chat history cleared!")
                st.rerun()
    
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
            with st.expander("📝 Provide Feedback", expanded=False):
                with st.form(f"feedback_form_{session_id}"):
                    if explanation_given:
                        was_needed = st.radio(
                            "Was this explanation necessary?",
                            ["Yes", "No"],
                            key=f"needed_{session_id}"
                        )
                        
                        was_helpful = None
                        if was_needed == "Yes":
                            was_helpful = st.radio(
                                "Was it helpful?",
                                ["Yes", "No"],
                                key=f"helpful_{session_id}"
                            )
                    else:
                        would_have_been_needed = st.radio(
                            "Would an explanation have been helpful?",
                            ["Yes", "No"],
                            key=f"would_need_{session_id}"
                        )
                    
                    if st.form_submit_button("Submit Feedback"):
                        if explanation_given:
                            feedback = ExplanationFeedback.create_feedback(
                                user_id=user_id,
                                session_id=session_id,
                                explanation_given=True,
                                was_needed=was_needed == "Yes",
                                was_helpful=was_helpful == "Yes" if was_helpful else None
                            )
                        else:
                            feedback = ExplanationFeedback.create_feedback(
                                user_id=user_id,
                                session_id=session_id,
                                explanation_given=False,
                                would_have_been_needed=would_have_been_needed == "Yes"
                            )
                        
                        feedback.save(self.db_config)
                        feedback_state['submitted'] = True
                        st.success("Thank you for your feedback!")
                        st.rerun()
    
    def load_user_chat_history(self, user_id: int, limit: int = 20):
        """Load recent chat history for user from PostgreSQL database."""
        try:
            if st.session_state.current_user_id != user_id:
                keys_to_remove = [key for key in st.session_state.keys() 
                                if key.startswith('chat_history_user_')]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.session_state.current_user_id = user_id
            
            existing_history = self._get_user_chat_history(user_id)
            if existing_history:
                return
            
            sessions = ChatSession.get_user_sessions(self.db_config, user_id, limit)
            
            chat_history = []
            for session in sessions:
                chat_history.append({
                    'session_id': session.id,
                    'user_message': session.user_message,
                    'system_response': session.system_response,
                    'explanation_given': session.explanation_given,
                    'timestamp': session.created_at,
                    'data': None  # Load from DB if needed
                })
            
            self._set_user_chat_history(user_id, list(reversed(chat_history)))
            
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")
            self._set_user_chat_history(user_id, [])