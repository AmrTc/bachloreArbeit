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
    
    # Strategy 1: Try PostgreSQL imports first (Docker/production - new structure)
    try:
        from src.database.postgres_models import ExplanationFeedback, User, ChatSession, ComprehensiveFeedback
        from src.utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: PostgreSQL imports successful")
        return ExplanationFeedback, User, ChatSession, None, AuthManager
    except ImportError as e:
        print(f"❌ PostgreSQL imports failed: {e}")
    
    # Strategy 2: Try relative PostgreSQL imports (fallback)
    try:
        from database.postgres_models import ExplanationFeedback, User, ChatSession, ComprehensiveFeedback
        from utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Relative PostgreSQL imports successful")
        return ExplanationFeedback, User, ChatSession, None, AuthManager
    except ImportError as e:
        print(f"❌ Relative PostgreSQL imports failed: {e}")
    
    # Strategy 3: Try direct imports (fallback to SQLite)
    try:
        from src.database.models import ExplanationFeedback, User, ChatSession
        from src.utils.path_utils import get_absolute_path
        from src.utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: SQLite fallback imports successful")
        return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
    except ImportError as e:
        print(f"❌ SQLite fallback imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.postgres_models import ExplanationFeedback, User, ChatSession, ComprehensiveFeedback
        from utils.auth_manager import AuthManager
        print("✅ Evaluation Dashboard: Manual path PostgreSQL imports successful")
        return ExplanationFeedback, User, ChatSession, None, AuthManager
    except ImportError as e:
        print(f"❌ Manual path PostgreSQL imports failed: {e}")
        try:
            from database.models import ExplanationFeedback, User, ChatSession
            from utils.path_utils import get_absolute_path
            from utils.auth_manager import AuthManager
            print("✅ Evaluation Dashboard: Manual path SQLite fallback successful")
            return ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager
        except ImportError as e2:
            print(f"❌ Manual path SQLite fallback failed: {e2}")
            st.error(f"❌ Could not import required modules: {e2}")
            st.stop()

# Import modules
ExplanationFeedback, User, ChatSession, get_absolute_path, AuthManager = robust_import_modules()

# Extract ComprehensiveFeedback from the import result
try:
    from src.database.postgres_models import ComprehensiveFeedback
except ImportError:
    try:
        from src.database.models import ComprehensiveFeedback
    except ImportError:
        ComprehensiveFeedback = None

# ComprehensiveFeedback is now imported in robust_import_modules()

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
    tab1, tab2 = st.tabs([
        "👥 User Analytics", 
        "💬 Feedback Analysis"
    ])
    
    with tab1:
        render_user_analytics_tab()
        
    with tab2:
        render_feedback_analysis_tab()



def render_user_analytics_tab():
    """Render user analytics and behavior patterns."""
    st.subheader("👥 User Behavior Analytics")
    
    # Get real user data
    auth_manager = AuthManager()
    db_config = auth_manager.db_config
    
    try:
        users = User.get_all_users(db_config)
        
        if users:
            # User role distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("User Role Distribution")
                role_counts = {}
                for user in users:
                    role_counts[user.role] = role_counts.get(user.role, 0) + 1
                
                if role_counts:
                    role_data = pd.DataFrame({
                        'Role': list(role_counts.keys()),
                        'Count': list(role_counts.values())
                    })
                    
                    fig = px.pie(
                        role_data, 
                        values='Count', 
                        names='Role',
                        title='User Distribution by Role'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No user data available")
            
            with col2:
                st.subheader("Assessment Completion Status")
                completed = sum(1 for user in users if user.has_completed_assessment)
                not_completed = len(users) - completed
                
                completion_data = pd.DataFrame({
                    'Status': ['Completed', 'Not Completed'],
                    'Count': [completed, not_completed]
                })
                
                fig = px.pie(
                    completion_data, 
                    values='Count', 
                    names='Status',
                    title='Assessment Completion Status'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # User demographics
            st.subheader("👤 User Demographics")
            
            # Age distribution
            age_counts = {}
            for user in users:
                if user.age:
                    age_counts[user.age] = age_counts.get(user.age, 0) + 1
            
            if age_counts:
                age_data = pd.DataFrame({
                    'Age': list(age_counts.keys()),
                    'Count': list(age_counts.values())
                })
                age_data = age_data.sort_values('Age')
                
                fig = px.bar(
                    age_data, 
                    x='Age', 
                    y='Count',
                    title='User Distribution by Age'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No age data available")
            
            # Gender distribution
            col1, col2 = st.columns(2)
            
            with col1:
                gender_counts = {}
                for user in users:
                    if user.gender:
                        gender_counts[user.gender] = gender_counts.get(user.gender, 0) + 1
                
                if gender_counts:
                    gender_data = pd.DataFrame({
                        'Gender': list(gender_counts.keys()),
                        'Count': list(gender_counts.values())
                    })
                    
                    fig = px.bar(
                        gender_data, 
                        x='Gender', 
                        y='Count',
                        title='User Distribution by Gender'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No gender data available")
            
            with col2:
                # Education level distribution
                education_counts = {}
                for user in users:
                    if user.education_level:
                        education_counts[user.education_level] = education_counts.get(user.education_level, 0) + 1
                
                if education_counts:
                    education_data = pd.DataFrame({
                        'Education Level': list(education_counts.keys()),
                        'Count': list(education_counts.values())
                    })
                    
                    fig = px.bar(
                        education_data, 
                        x='Education Level', 
                        y='Count',
                        title='User Distribution by Education Level'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No education data available")
            
            # User assessment levels
            st.subheader("📊 User Assessment Levels")
            level_counts = {}
            for user in users:
                if user.user_level_category:
                    level_counts[user.user_level_category] = level_counts.get(user.user_level_category, 0) + 1
            
            if level_counts:
                level_data = pd.DataFrame({
                    'Level': list(level_counts.keys()),
                    'Count': list(level_counts.values())
                })
                
                fig = px.bar(
                    level_data, 
                    x='Level', 
                    y='Count',
                    title='User Distribution by Assessment Level'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent user table with real data
            st.subheader("📋 Recent User Activity")
            
            # Prepare user data for display
            user_display_data = []
            for user in users[:10]:  # Show last 10 users
                user_display_data.append({
                    'Username': user.username,
                    'Role': user.role,
                    'Age': user.age or 'Not Specified',
                    'Assessment Level': user.user_level_category or 'Not Assessed',
                    'Gender': user.gender or 'Not Specified',
                    'Profession': user.profession or 'Not Specified',
                    'Education': user.education_level or 'Not Specified',
                    'Created': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
                })
            
            if user_display_data:
                user_df = pd.DataFrame(user_display_data)
                st.dataframe(user_df, use_container_width=True)
            else:
                st.info("No user data available")
                
        else:
            st.info("No users found in the database")
            
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        # Fallback to sample data
        st.subheader("📋 Sample User Data (Fallback)")
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
    
    # Get database path
    try:
        auth_manager = AuthManager()
        db_config = auth_manager.db_config
    except:
        # Fallback to default PostgreSQL config
        from src.database.postgres_config import PostgresConfig
        pg_config = PostgresConfig()
        db_config = pg_config.get_connection_params()
    
    # Explanation Feedback Analysis
    st.markdown("### 📝 Explanation Feedback Analysis")
    
    if ExplanationFeedback:
        feedback_data = ExplanationFeedback.get_all_feedback(db_config)
        
        if feedback_data:
            # Convert to DataFrame for analysis
            feedback_df = pd.DataFrame([
                {
                    'Username': getattr(fb, 'username', 'Unknown'),
                    'Explanation Given': fb.explanation_given,
                    'Was Needed': fb.was_needed,
                    'Was Helpful': fb.was_helpful,
                    'Would Have Been Needed': fb.would_have_been_needed,
                    'Date': fb.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for fb in feedback_data
            ])
            
            st.dataframe(feedback_df, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Feedback", len(feedback_data))
            with col2:
                explanations_given = sum(1 for fb in feedback_data if fb.explanation_given)
                st.metric("Explanations Given", explanations_given)
            with col3:
                helpful_explanations = sum(1 for fb in feedback_data if fb.was_helpful)
                st.metric("Helpful Explanations", helpful_explanations)
        else:
            st.info("No explanation feedback data available yet.")
    else:
        st.warning("ExplanationFeedback model not available.")
    
    # Comprehensive Research Feedback Analysis
    st.markdown("### 🔬 Comprehensive Research Feedback Analysis")
    
    if ComprehensiveFeedback:
        comprehensive_feedback_data = ComprehensiveFeedback.get_all_feedback(db_config)
        
        if comprehensive_feedback_data:
            # Convert to DataFrame for analysis
            comp_feedback_df = pd.DataFrame([
                {
                    'Username': getattr(fb, 'username', 'Unknown'),
                    'Frequency Rating': fb.frequency_rating,
                    'Explanation Quality': fb.explanation_quality_rating,
                    'System Helpfulness': fb.system_helpfulness_rating,
                    'Learning Improvement': fb.learning_improvement_rating,
                    'Auto Explanation': fb.auto_explanation,
                    'System Accuracy': fb.system_accuracy,
                    'Recommendation': fb.recommendation,
                    'Date': fb.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for fb in comprehensive_feedback_data
            ])
            
            st.dataframe(comp_feedback_df, use_container_width=True)
            
            # Summary statistics for comprehensive feedback
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Research Feedback", len(comprehensive_feedback_data))
            with col2:
                avg_quality = sum(fb.explanation_quality_rating for fb in comprehensive_feedback_data) / len(comprehensive_feedback_data)
                st.metric("Avg. Explanation Quality", f"{avg_quality:.1f}/5")
            with col3:
                avg_helpfulness = sum(fb.system_helpfulness_rating for fb in comprehensive_feedback_data) / len(comprehensive_feedback_data)
                st.metric("Avg. System Helpfulness", f"{avg_helpfulness:.1f}/5")
            with col4:
                positive_recommendations = sum(1 for fb in comprehensive_feedback_data if fb.recommendation == 'Yes')
                st.metric("Positive Recommendations", f"{positive_recommendations}/{len(comprehensive_feedback_data)}")
            
            # Detailed feedback analysis
            st.markdown("#### 📊 Detailed Feedback Analysis")
            
            # Frequency rating distribution
            st.subheader("Explanation Frequency Preferences")
            frequency_counts = comp_feedback_df['Frequency Rating'].value_counts().sort_index()
            st.bar_chart(frequency_counts)
            
            # Explanation quality distribution
            st.subheader("Explanation Quality Ratings")
            quality_counts = comp_feedback_df['Explanation Quality'].value_counts().sort_index()
            st.bar_chart(quality_counts)
            
            # System helpfulness distribution
            st.subheader("System Helpfulness Ratings")
            helpfulness_counts = comp_feedback_df['System Helpfulness'].value_counts().sort_index()
            st.bar_chart(helpfulness_counts)
            
            # Learning improvement distribution
            st.subheader("Learning Improvement Ratings")
            learning_counts = comp_feedback_df['Learning Improvement'].value_counts().sort_index()
            st.bar_chart(learning_counts)
            
            # Auto-explanation preferences
            st.subheader("Auto-Explanation Preferences")
            auto_explanation_counts = comp_feedback_df['Auto Explanation'].value_counts()
            st.bar_chart(auto_explanation_counts)
            
            # System accuracy beliefs
            st.subheader("System Accuracy Beliefs")
            accuracy_counts = comp_feedback_df['System Accuracy'].value_counts()
            st.bar_chart(accuracy_counts)
            
            # Recommendations
            st.subheader("System Recommendations")
            recommendation_counts = comp_feedback_df['Recommendation'].value_counts()
            st.bar_chart(recommendation_counts)
            
        else:
            st.info("No comprehensive research feedback data available yet.")
    else:
        st.warning("ComprehensiveFeedback model not available.")



if __name__ == "__main__":
    render_evaluation_dashboard() 