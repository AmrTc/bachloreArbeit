import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Robust import function
def robust_import_modules():
    """Import required modules with multiple fallback strategies."""
    
    # Strategy 1: Try absolute imports (local development)
    try:
from new_data_assistant_project.src.database.models import ExplanationFeedback, User, ChatSession
from new_data_assistant_project.src.utils.path_utils import get_absolute_path
from new_data_assistant_project.src.utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Absolute imports successful")
        return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    # Strategy 2: Try direct imports (Docker/production - new structure)
    try:
        from src.database.models import ExplanationFeedback, User, ChatSession
        from src.utils.path_utils import get_absolute_path
        from src.utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Direct imports successful")
        return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    # Strategy 3: Try relative imports (fallback)
    try:
        from src.database.models import ExplanationFeedback, User, ChatSession
        from src.utils.path_utils import get_absolute_path
        from src.utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Relative imports successful")
        return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.models import ExplanationFeedback, User, ChatSession
        from utils.path_utils import get_absolute_path
        from utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Manual path imports successful")
        return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager = robust_import_modules()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_evaluation_dashboard():
    """Main function to render the evaluation dashboard."""
    st.header("📊 Evaluation Dashboard")
    
    # Get current user for access control
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user or current_user.role != 'admin':
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview", 
        "👥 User Analytics", 
        "💬 Feedback Analysis", 
        "📊 System Metrics"
    ])
    
    with tab1:
        render_overview_tab()
        
        with tab2:
        render_user_analytics_tab()
        
        with tab3:
        render_feedback_analysis_tab()
        
        with tab4:
        render_system_metrics_tab()

def render_overview_tab():
    """Render the overview tab with key metrics."""
    st.subheader("🎯 Key Performance Indicators")
    
    # Create metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    # Sample data - replace with actual database queries
    with col1:
        st.metric(
            label="Total Users",
            value="42",
            delta="5 this week"
        )
    
    with col2:
        st.metric(
            label="Chat Sessions",
            value="156",
            delta="23 today"
        )
    
    with col3:
        st.metric(
            label="Average Rating",
            value="4.2",
            delta="0.3"
        )
    
    with col4:
        st.metric(
            label="System Uptime",
            value="99.8%",
            delta="0.1%"
        )
    
    # Activity chart
    st.subheader("📈 Activity Trends")
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    activity_data = pd.DataFrame({
        'Date': dates,
        'Sessions': [15, 23, 18, 31, 25, 19, 28] * 4 + [20, 25, 22]
    })
    
    fig = px.line(
        activity_data, 
        x='Date', 
        y='Sessions',
        title='Daily Chat Sessions'
    )
    st.plotly_chart(fig, use_container_width=True)

def render_user_analytics_tab():
    """Render user analytics and behavior patterns."""
    st.subheader("👥 User Behavior Analytics")
    
    # User distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("User Role Distribution")
        role_data = pd.DataFrame({
            'Role': ['Admin', 'Regular User', 'Power User'],
            'Count': [5, 32, 5]
        })
        
        fig = px.pie(
            role_data, 
            values='Count', 
            names='Role',
            title='User Distribution by Role'
        )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("User Activity Levels")
        activity_data = pd.DataFrame({
            'Activity Level': ['High', 'Medium', 'Low'],
            'Users': [12, 20, 10]
        })
        
        fig = px.bar(
            activity_data, 
            x='Activity Level', 
            y='Users',
            title='User Activity Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent user table
    st.subheader("📋 Recent User Activity")
    
    # Sample data - replace with actual user queries
    recent_users = pd.DataFrame({
        'Username': ['user1', 'user2', 'user3', 'admin1', 'user4'],
        'Last Active': ['2024-01-15 14:30', '2024-01-15 12:15', '2024-01-14 16:45', '2024-01-15 09:20', '2024-01-13 11:30'],
        'Sessions': [15, 8, 23, 45, 3],
        'Status': ['Active', 'Active', 'Inactive', 'Active', 'New']
    })
    
    st.dataframe(recent_users, use_container_width=True)

def render_feedback_analysis_tab():
    """Render feedback analysis and sentiment trends."""
    st.subheader("💬 User Feedback Analysis")
    
    # Feedback metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Feedback", "89", "12 this week")
    
    with col2:
        st.metric("Avg. Rating", "4.1", "0.2")
    
    with col3:
        st.metric("Response Rate", "67%", "5%")
    
    # Feedback trends
    st.subheader("📊 Feedback Trends")
    
    feedback_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
        'Positive': [8, 12, 6, 15, 9, 11, 13] * 4 + [10, 14],
        'Neutral': [3, 5, 2, 4, 6, 3, 5] * 4 + [4, 3],
        'Negative': [1, 2, 1, 3, 1, 2, 1] * 4 + [2, 1]
    })
    
    fig = px.line(
        feedback_data, 
        x='Date', 
        y=['Positive', 'Neutral', 'Negative'],
        title='Feedback Sentiment Over Time'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top feedback categories
    st.subheader("🏷️ Feedback Categories")
    
    categories = pd.DataFrame({
        'Category': ['Ease of Use', 'Accuracy', 'Speed', 'Features', 'Interface'],
        'Count': [25, 20, 15, 12, 8],
        'Avg Rating': [4.2, 4.5, 3.8, 4.0, 4.3]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(categories, x='Category', y='Count', title='Feedback by Category')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(categories, x='Category', y='Avg Rating', title='Average Rating by Category')
            st.plotly_chart(fig, use_container_width=True)

def render_system_metrics_tab():
    """Render system performance and technical metrics."""
    st.subheader("🔧 System Performance Metrics")
    
    # System health indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Response Time", "1.2s", "-0.3s")
    
    with col2:
        st.metric("Error Rate", "0.8%", "-0.2%")
    
    with col3:
        st.metric("CPU Usage", "45%", "5%")
    
    with col4:
        st.metric("Memory Usage", "62%", "3%")
    
    # Performance trends
    st.subheader("📈 Performance Trends")
    
    perf_data = pd.DataFrame({
        'Time': pd.date_range(start='2024-01-15 00:00', periods=24, freq='H'),
        'Response Time (ms)': [1200, 1150, 1300, 1100, 1250, 1180, 1220] * 3 + [1190, 1160, 1140],
        'CPU Usage (%)': [45, 42, 48, 40, 46, 44, 47] * 3 + [43, 41, 39],
        'Memory Usage (%)': [62, 60, 65, 58, 63, 61, 64] * 3 + [59, 57, 55]
    })
    
    # Response time chart
    fig = px.line(
        perf_data, 
        x='Time', 
        y='Response Time (ms)',
        title='System Response Time (24h)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Resource usage
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(perf_data, x='Time', y='CPU Usage (%)', title='CPU Usage')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(perf_data, x='Time', y='Memory Usage (%)', title='Memory Usage')
        st.plotly_chart(fig, use_container_width=True)
    
    # System logs (sample)
    st.subheader("📝 Recent System Events")
    
    logs = pd.DataFrame({
        'Timestamp': ['2024-01-15 14:30:00', '2024-01-15 14:25:00', '2024-01-15 14:20:00'],
        'Level': ['INFO', 'WARNING', 'INFO'],
        'Message': [
            'User login successful',
            'High memory usage detected',
            'Database backup completed'
        ]
    })
    
    st.dataframe(logs, use_container_width=True)

if __name__ == "__main__":
    render_evaluation_dashboard() 