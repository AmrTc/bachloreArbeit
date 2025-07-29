import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Import with fallback for Docker compatibility
try:
    # Try absolute imports first (for local development)
    from new_data_assistant_project.src.database.models import ExplanationFeedback, User, ChatSession
    from new_data_assistant_project.src.utils.path_utils import get_absolute_path
    from new_data_assistant_project.src.utils.auth_manager import AuthManager
except ImportError:
    # Fallback to relative imports (for Docker/production)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.database.models import ExplanationFeedback, User, ChatSession
    from src.utils.path_utils import get_absolute_path
    from src.utils.auth_manager import AuthManager

logger = logging.getLogger(__name__)

def render_evaluation_dashboard():
    """Render the admin evaluation dashboard."""
    auth_manager = AuthManager()
    
    # Check admin authentication
    if not auth_manager.is_authenticated() or not auth_manager.is_admin():
        st.error("🚫 Access denied. Admin privileges required.")
        return
    
    st.title("📊 Evaluation Dashboard")
    st.markdown("### System Performance & User Feedback Analysis")
    
    db_path = get_absolute_path('src/database/superstore.db')
    
    # Load data
    try:
        feedback_data = ExplanationFeedback.get_all_feedback(db_path)
        
        if not feedback_data:
            st.warning("📋 No feedback data available yet.")
            return
        
        # Convert to DataFrame for analysis
        df_feedback = pd.DataFrame([{
            'user_id': f.user_id,
            'username': f.username,
            'session_id': f.session_id,
            'user_message': f.user_message,
            'explanation_given': f.explanation_given,
            'was_needed': f.was_needed,
            'was_helpful': f.was_helpful,
            'would_have_been_needed': f.would_have_been_needed,
            'timestamp': f.created_at
        } for f in feedback_data])
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "👥 User Analysis", "📋 Detailed Feedback", "📊 Export Data"])
        
        with tab1:
            render_overview_tab(df_feedback)
        
        with tab2:
            render_user_analysis_tab(df_feedback, db_path)
        
        with tab3:
            render_detailed_feedback_tab(df_feedback)
        
        with tab4:
            render_export_tab(df_feedback, db_path)
            
    except Exception as e:
        st.error(f"❌ Error loading dashboard data: {e}")
        logger.error(f"Dashboard error: {e}")

def render_overview_tab(df_feedback):
    """Render overview statistics."""
    st.subheader("📈 System Performance Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_interactions = len(df_feedback)
        st.metric("Total Interactions", total_interactions)
    
    with col2:
        explanations_given = len(df_feedback[df_feedback['explanation_given'] == True])
        explanation_rate = (explanations_given / total_interactions * 100) if total_interactions > 0 else 0
        st.metric("Explanations Given", f"{explanations_given} ({explanation_rate:.1f}%)")
    
    with col3:
        unique_users = df_feedback['user_id'].nunique()
        st.metric("Active Users", unique_users)
    
    with col4:
        recent_interactions = len(df_feedback[df_feedback['timestamp'] >= datetime.now() - timedelta(days=7)])
        st.metric("Last 7 Days", recent_interactions)
    
    # Explanation effectiveness charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Explanation Effectiveness")
        
        # For interactions where explanations were given
        explained = df_feedback[df_feedback['explanation_given'] == True]
        if len(explained) > 0:
            effectiveness_data = []
            
            needed_yes = len(explained[explained['was_needed'] == True])
            needed_no = len(explained[explained['was_needed'] == False])
            
            helpful_yes = len(explained[explained['was_helpful'] == True])
            helpful_no = len(explained[explained['was_helpful'] == False])
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Needed',
                x=['Yes', 'No'],
                y=[needed_yes, needed_no],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Helpful',
                x=['Yes', 'No'],
                y=[helpful_yes, helpful_no],
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title="Explanation Feedback",
                xaxis_title="Response",
                yaxis_title="Count",
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No explanation feedback data available yet.")
    
    with col2:
        st.subheader("📊 Missing Explanations Analysis")
        
        # For interactions where no explanations were given
        not_explained = df_feedback[df_feedback['explanation_given'] == False]
        if len(not_explained) > 0:
            would_need_yes = len(not_explained[not_explained['would_have_been_needed'] == True])
            would_need_no = len(not_explained[not_explained['would_have_been_needed'] == False])
            
            fig = px.pie(
                values=[would_need_yes, would_need_no],
                names=['Would have been helpful', 'Not needed'],
                title="Would Explanation Have Helped?"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("All interactions included explanations.")
    
    # Timeline chart
    st.subheader("📅 Interaction Timeline")
    df_feedback['date'] = pd.to_datetime(df_feedback['timestamp']).dt.date
    timeline_data = df_feedback.groupby(['date', 'explanation_given']).size().reset_index(name='count')
    
    fig = px.line(timeline_data, x='date', y='count', color='explanation_given',
                  title="Daily Interactions (With/Without Explanations)")
    st.plotly_chart(fig, use_container_width=True)

def render_user_analysis_tab(df_feedback, db_path):
    """Render user-specific analysis."""
    st.subheader("👥 User Performance Analysis")
    
    # User statistics
    user_stats = df_feedback.groupby(['user_id', 'username']).agg({
        'session_id': 'count',
        'explanation_given': ['sum', lambda x: (x == True).mean()],
        'was_needed': lambda x: x.sum() if x.notna().any() else 0,
        'was_helpful': lambda x: x.sum() if x.notna().any() else 0
    }).round(2)
    
    user_stats.columns = ['Total_Interactions', 'Explanations_Received', 'Explanation_Rate', 
                         'Needed_Count', 'Helpful_Count']
    user_stats = user_stats.reset_index()
    
    # Load user expertise levels
    import sqlite3
    conn = sqlite3.connect(db_path)
    users_df = pd.read_sql_query("""
        SELECT id, username, sql_expertise_level, domain_knowledge, 
               has_completed_assessment, created_at
        FROM users WHERE role = 'user'
    """, conn)
    conn.close()
    
    # Merge with user data
    if not users_df.empty:
        user_stats = user_stats.merge(
            users_df[['id', 'sql_expertise_level', 'domain_knowledge', 'has_completed_assessment']], 
            left_on='user_id', right_on='id', how='left'
        )
    
    st.subheader("📋 User Statistics Table")
    st.dataframe(user_stats, use_container_width=True)
    
    # User performance visualization
    col1, col2 = st.columns(2)
    
    with col1:
        if 'sql_expertise_level' in user_stats.columns:
            fig = px.scatter(user_stats, x='sql_expertise_level', y='Explanation_Rate',
                           size='Total_Interactions', hover_data=['username'],
                           title="Explanation Rate vs SQL Expertise")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'sql_expertise_level' in user_stats.columns:
            fig = px.box(user_stats, x='sql_expertise_level', y='Total_Interactions',
                        title="Interaction Count by SQL Expertise Level")
            st.plotly_chart(fig, use_container_width=True)

def render_detailed_feedback_tab(df_feedback):
    """Render detailed feedback data."""
    st.subheader("📋 Detailed Feedback Records")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_users = st.multiselect(
            "Filter by User:",
            options=df_feedback['username'].unique(),
            default=[]
        )
    
    with col2:
        explanation_filter = st.selectbox(
            "Explanation Given:",
            options=['All', 'Yes', 'No']
        )
    
    with col3:
        date_range = st.date_input(
            "Date Range:",
            value=(df_feedback['timestamp'].min().date(), df_feedback['timestamp'].max().date()),
            max_value=datetime.now().date()
        )
    
    # Apply filters
    filtered_df = df_feedback.copy()
    
    if selected_users:
        filtered_df = filtered_df[filtered_df['username'].isin(selected_users)]
    
    if explanation_filter != 'All':
        filtered_df = filtered_df[filtered_df['explanation_given'] == (explanation_filter == 'Yes')]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['timestamp'].dt.date >= start_date) & 
            (filtered_df['timestamp'].dt.date <= end_date)
        ]
    
    # Display filtered data
    st.markdown(f"**Found {len(filtered_df)} records**")
    
    if len(filtered_df) > 0:
        display_columns = ['timestamp', 'username', 'user_message', 'explanation_given', 
                          'was_needed', 'was_helpful', 'would_have_been_needed']
        st.dataframe(filtered_df[display_columns], use_container_width=True)
    else:
        st.info("No records match the selected filters.")

def render_export_tab(df_feedback, db_path):
    """Render data export options."""
    st.subheader("📊 Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Download Feedback Data")
        
        # Convert timestamps to string for CSV export
        export_df = df_feedback.copy()
        export_df['timestamp'] = export_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Feedback CSV",
            data=csv,
            file_name=f"explanation_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("### 📊 Export Summary Report")
        
        # Generate summary report
        report_lines = [
            f"# Explanation System Evaluation Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"## Summary Statistics",
            f"- Total Interactions: {len(df_feedback)}",
            f"- Explanations Given: {len(df_feedback[df_feedback['explanation_given'] == True])}",
            f"- Unique Users: {df_feedback['user_id'].nunique()}",
            "",
            f"## Explanation Effectiveness",
        ]
        
        explained = df_feedback[df_feedback['explanation_given'] == True]
        if len(explained) > 0:
            needed_rate = explained['was_needed'].mean() * 100 if explained['was_needed'].notna().any() else 0
            helpful_rate = explained['was_helpful'].mean() * 100 if explained['was_helpful'].notna().any() else 0
            report_lines.extend([
                f"- Explanations Needed: {needed_rate:.1f}%",
                f"- Explanations Helpful: {helpful_rate:.1f}%"
            ])
        
        report_text = "\n".join(report_lines)
        
        st.download_button(
            label="📋 Download Summary Report",
            data=report_text,
            file_name=f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )

if __name__ == "__main__":
    render_evaluation_dashboard() 