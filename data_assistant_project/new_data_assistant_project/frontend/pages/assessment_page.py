import streamlit as st
from typing import Optional, Dict, Any
import logging

# Robust import function
def robust_import_modules():
    """Import required modules with multiple fallback strategies."""
    
    # Strategy 1: Try absolute imports (local development)
    try:
        from new_data_assistant_project.src.database.models import User
        from new_data_assistant_project.src.utils.auth_manager import AuthManager
        print("✅ Assessment Page: Absolute imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Absolute imports failed: {e}")
    
    # Strategy 2: Try direct imports (Docker/production - new structure)
    try:
        from src.database.models import User
        from src.utils.auth_manager import AuthManager
        print("✅ Assessment Page: Direct imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Direct imports failed: {e}")
    
    # Strategy 3: Try relative imports (fallback)
    try:
        from src.database.models import User
        from src.utils.auth_manager import AuthManager
        print("✅ Assessment Page: Relative imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Relative imports failed: {e}")
    
    # Strategy 4: Manual path manipulation
    try:
        import sys
        from pathlib import Path
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        sys.path.insert(0, str(current_dir / 'src'))
        
        from database.models import User
        from utils.auth_manager import AuthManager
        print("✅ Assessment Page: Manual path imports successful")
        return User, AuthManager
    except ImportError as e:
        print(f"❌ Manual path imports failed: {e}")
        st.error(f"❌ Could not import required modules: {e}")
        st.stop()

# Import modules
User, AuthManager = robust_import_modules()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_assessment_page(user: User):
    """Render the comprehensive assessment page for the research study."""
    # Ensure we have database config available for saving results
    auth_manager = AuthManager()
    
    st.markdown("""
    # 📊 Assessment Phase
    
    ## Understanding Your Expertise Level
    
    This assessment helps us understand your expertise in key areas relevant to data analysis.
    Your responses will help us provide the most appropriate level of assistance for my bachlore thesis.
    
    **Duration:** Approximately 5 minutes
    
    ---
    """)
    
    # Initialize session state for assessment
    if 'assessment_step' not in st.session_state:
        st.session_state.assessment_step = 0
    if 'assessment_scores' not in st.session_state:
        st.session_state.assessment_scores = {}
    
    # Assessment steps
    steps = [
        "user_demographics",  # New step for user information
        "sql_expertise",      # New step for SQL expertise assessment
        "data_analysis_fundamentals", 
        "business_analytics",
        "forecasting_statistics",
        "data_visualization",
        "domain_knowledge_retail",
        "completion"
    ]
    
    current_step = steps[st.session_state.assessment_step]

    # User Demographics Information
    if current_step == "user_demographics":
        st.markdown("### 👤 General Information")
        st.markdown("Please provide some basic information about yourself. This helps us better understand your background, provide more appropriate assistance, and is necessary for my bachlore thesis.")
        
        # Age input
        age = st.number_input(
            "Age:",
            min_value=13,
            max_value=100,
            value=st.session_state.get('age', 25),
            help="Please enter your age (13-100)",
            key="age_input"
        )
        
        # Gender selection
        gender = st.selectbox(
            "Gender:",
            ["", "Male", "Female", "Non-binary", "Prefer not to say"],
            key="gender_select"
        )
        
        # Profession input
        profession = st.text_input(
            "Profession/Job Title:",
            value=st.session_state.get('profession', ''),
            placeholder="e.g., Data Analyst, Student, Business Manager, etc.",
            key="profession_input"
        )
        
        # Education level
        education_level = st.text_input(
            "Education Level:",
            value=st.session_state.get('education_level', ''),
            placeholder="e.g., none, a-level,Bachelor's, Master's, etc.",
            key="education_level_input"
        )
        
        # Study/Training field
        study_training = st.text_input(
            "Field of Study/Training:",
            value=st.session_state.get('study_training', ''),
            placeholder="e.g.,none, Computer Science, Business Administration, Statistics, etc.",
            key="study_training_input"
        )
        
        # Store in session state
        st.session_state.user_demographics = {
            'age': age,
            'gender': gender if gender else None,
            'profession': profession if profession else None,
            'education_level': education_level if education_level else None,
            'study_training': study_training if study_training else None
        }
        
        if st.button("Continue to Assessment", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()

    # SQL Expertise Assessment
    elif current_step == "sql_expertise":
        st.markdown("### 💻 SQL Expertise Assessment")
        st.markdown("Please rate your SQL knowledge and experience level.")
        
        # Self-assessment rating
        sql_self_rating = st.slider(
            "Rate your SQL expertise level (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('sql_expertise_rating', 3),
            help="1 = No SQL experience, 5 = Expert level"
        )
        
        # SQL concept familiarity
        sql_concept_1 = st.radio(
            "Are you familiar with basic SELECT statements and WHERE clauses?",
            ["Yes", "Somewhat", "No"],
            key="sql_concept_1"
        )
        
        sql_concept_2 = st.radio(
            "Do you know how to use JOINs and GROUP BY clauses?",
            ["Yes", "Somewhat", "No"],
            key="sql_concept_2"
        )
        
        sql_concept_3 = st.radio(
            "Have you worked with subqueries or advanced SQL functions?",
            ["Yes", "Somewhat", "No"],
            key="sql_concept_3"
        )
        
        # Calculate SQL expertise score
        sql_score = 0
        if sql_self_rating >= 4:
            sql_score = 4
        elif sql_self_rating == 3:
            sql_score = 2
        else:
            sql_score = 1
        
        # Adjust based on concept familiarity
        if sql_concept_1 == "Yes" and sql_concept_2 == "Yes" and sql_concept_3 == "Yes":
            sql_score = min(5, sql_score + 1)
        elif sql_concept_1 == "No" or sql_concept_2 == "No":
            sql_score = max(0, sql_score - 1)
        
        st.session_state.assessment_scores['sql_expertise'] = sql_score
        st.session_state.assessment_scores['sql_expertise_rating'] = sql_self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Data Analysis Fundamentals
    if current_step == "data_analysis_fundamentals":
        st.markdown("### 📈 Data Analysis Fundamentals")
        # Self-assessment rating
        self_rating = st.slider(
            "Rate your data analysis fundamentals (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('data_analysis_fundamentals_rating', 3),
            help="1 = No experience, 5 = Expert level"
        )
        
        # Concept familiarity
        concept_1 = st.radio(
            "Are you familiar with mean, median, mode, and standard deviation?",
            ["Yes", "Somewhat", "No"],
            key="concept_1"
        )
        
        concept_2 = st.radio(
            "Do you know what data outliers are and how to handle them?",
            ["Yes", "Somewhat", "No"],
            key="concept_2"
        )
        
        # Calculate score
        score = 0
        if self_rating >= 4:
            score = 4
        elif self_rating == 3:
            score = 2
        else:
            score = 1
        
        # Adjust based on concept familiarity
        if concept_1 == "Yes" and concept_2 == "Yes":
            score = min(4, score + 1)
        elif concept_1 == "No" or concept_2 == "No":
            score = max(0, score - 1)
        
        st.session_state.assessment_scores['data_analysis_fundamentals'] = score
        st.session_state.assessment_scores['data_analysis_fundamentals_rating'] = self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Business Analytics
    elif current_step == "business_analytics":
        st.markdown("### 💼 Business Analytics")
        
        # Self-assessment rating
        self_rating = st.slider(
            "Rate your business analytics knowledge (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('business_analytics_rating', 3),
            help="1 = No experience, 5 = Expert level"
        )
        
        # Concept familiarity
        concept_1 = st.radio(
            "Are you familiar with Customer Lifetime Value (CLV)?",
            ["Yes", "Somewhat", "No"],
            key="ba_concept_1"
        )
        
        concept_2 = st.radio(
            "Do you understand profit margins and how to calculate them?",
            ["Yes", "Somewhat", "No"],
            key="ba_concept_2"
        )
        
        # Calculate score
        score = 0
        if self_rating >= 4:
            score = 4
        elif self_rating == 3:
            score = 2
        else:
            score = 1
        
        # Adjust based on concept familiarity
        if concept_1 == "Yes" and concept_2 == "Yes":
            score = min(4, score + 1)
        elif concept_1 == "No" or concept_2 == "No":
            score = max(0, score - 1)
        
        st.session_state.assessment_scores['business_analytics'] = score
        st.session_state.assessment_scores['business_analytics_rating'] = self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Forecasting & Statistics
    elif current_step == "forecasting_statistics":
        st.markdown("### 📉 Forecasting & Statistics")
        
        # Self-assessment rating
        self_rating = st.slider(
            "Rate your statistics and forecasting knowledge (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('forecasting_statistics_rating', 3),
            help="1 = No experience, 5 = Expert level"
        )
        
        # Concept familiarity
        concept_1 = st.radio(
            "Have you used forecasting models before?",
            ["Yes", "Somewhat", "No"],
            key="fs_concept_1"
        )
        
        concept_2 = st.radio(
            "Do you understand hypothesis testing and confidence intervals?",
            ["Yes", "Somewhat", "No"],
            key="fs_concept_2"
        )
        
        # Calculate score
        score = 0
        if self_rating >= 4:
            score = 4
        elif self_rating == 3:
            score = 2
        else:
            score = 1
        
        # Adjust based on concept familiarity
        if concept_1 == "Yes" and concept_2 == "Yes":
            score = min(4, score + 1)
        elif concept_1 == "No" or concept_2 == "No":
            score = max(0, score - 1)
        
        st.session_state.assessment_scores['forecasting_statistics'] = score
        st.session_state.assessment_scores['forecasting_statistics_rating'] = self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Data Visualization
    elif current_step == "data_visualization":
        st.markdown("### 📊 Data Visualization")
        
        # Self-assessment rating
        self_rating = st.slider(
            "Rate your data visualization skills (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('data_visualization_rating', 3),
            help="1 = No experience, 5 = Expert level"
        )
        
        # Concept familiarity
        concept_1 = st.radio(
            "Are you familiar with visualization best practices?",
            ["Yes", "Somewhat", "No"],
            key="dv_concept_1"
        )
        
        concept_2 = st.radio(
            "Have you used tools like Tableau, Power BI, or Matplotlib?",
            ["Yes", "Somewhat", "No"],
            key="dv_concept_2"
        )
        
        # Calculate score
        score = 0
        if self_rating >= 4:
            score = 4
        elif self_rating == 3:
            score = 2
        else:
            score = 1
        
        # Adjust based on concept familiarity
        if concept_1 == "Yes" and concept_2 == "Yes":
            score = min(4, score + 1)
        elif concept_1 == "No" or concept_2 == "No":
            score = max(0, score - 1)
        
        st.session_state.assessment_scores['data_visualization'] = score
        st.session_state.assessment_scores['data_visualization_rating'] = self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Domain Knowledge - Retail
    elif current_step == "domain_knowledge_retail":
        st.markdown("### 🛒 Domain Knowledge: Retail")
        
        # Self-assessment rating
        self_rating = st.slider(
            "Rate your retail domain knowledge (1-5):",
            min_value=1,
            max_value=5,
            value=st.session_state.assessment_scores.get('domain_knowledge_retail_rating', 3),
            help="1 = No experience, 5 = Expert level"
        )
        
        # Concept familiarity
        concept_1 = st.radio(
            "Have you worked with retail sales data before?",
            ["Yes", "Somewhat", "No"],
            key="rk_concept_1"
        )
        
        concept_2 = st.radio(
            "Do you understand common retail metrics?",
            ["Yes", "Somewhat", "No"],
            key="rk_concept_2"
        )
        
        # Calculate score
        score = 0
        if self_rating >= 4:
            score = 4
        elif self_rating == 3:
            score = 2
        else:
            score = 1
        
        # Adjust based on concept familiarity
        if concept_1 == "Yes" and concept_2 == "Yes":
            score = min(4, score + 1)
        elif concept_1 == "No" or concept_2 == "No":
            score = max(0, score - 1)
        
        st.session_state.assessment_scores['domain_knowledge_retail'] = score
        st.session_state.assessment_scores['domain_knowledge_retail_rating'] = self_rating
        
        if st.button("Continue", type="primary"):
            st.session_state.assessment_step += 1
            st.rerun()
    
    # Completion step
    elif current_step == "completion":
        st.markdown("### ✅ Assessment Complete")
        
        # Calculate total score
        total_score = sum([
            st.session_state.assessment_scores.get('sql_expertise', 0),
            st.session_state.assessment_scores.get('data_analysis_fundamentals', 0),
            st.session_state.assessment_scores.get('business_analytics', 0),
            st.session_state.assessment_scores.get('forecasting_statistics', 0),
            st.session_state.assessment_scores.get('data_visualization', 0),
            st.session_state.assessment_scores.get('domain_knowledge_retail', 0)
        ])
        
        # Determine user level
        if total_score <= 5:
            level = "Beginner"
        elif total_score <= 10:
            level = "Novice"
        elif total_score <= 15:
            level = "Intermediate"
        elif total_score <= 20:
            level = "Advanced"
        else:
            level = "Expert"
        
        st.markdown("### Your Results")
        st.write(f"- **Total Score**: {total_score}/30")
        st.write(f"- **User Level**: {level}")
        
        if st.button("Save and Continue", type="primary"):
            # First, save user demographics information
            if hasattr(st.session_state, 'user_demographics') and st.session_state.user_demographics:
                demographics = st.session_state.user_demographics
                user.update_user_demographics(
                    db_config=auth_manager.db_config,
                    age=demographics.get('age'),
                    gender=demographics.get('gender'),
                    profession=demographics.get('profession'),
                    education_level=demographics.get('education_level'),
                    study_training=demographics.get('study_training')
                )
            
            # Save assessment results to user profile
            domain_scores = {
                'sql_expertise': st.session_state.assessment_scores.get('sql_expertise', 0),
                'data_analysis_fundamentals': st.session_state.assessment_scores.get('data_analysis_fundamentals', 0),
                'business_analytics': st.session_state.assessment_scores.get('business_analytics', 0),
                'forecasting_statistics': st.session_state.assessment_scores.get('forecasting_statistics', 0),
                'data_visualization': st.session_state.assessment_scores.get('data_visualization', 0),
                'domain_knowledge_retail': st.session_state.assessment_scores.get('domain_knowledge_retail', 0)
            }
            
            user.complete_comprehensive_assessment(
                db_config=auth_manager.db_config,
                domain_scores=domain_scores
            )
            st.success("Assessment results and user information saved! Proceeding to Task Phase.")
            # Navigate to Task page
            st.session_state.assessment_step = 0
            st.session_state.current_page = "task"
            st.rerun() 

    # Navigation
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Welcome"):
            st.session_state.current_page = "welcome"
            st.rerun()
    
    with col2:
        if st.button("Assessment"):
            st.session_state.current_page = "assessment"
            st.rerun()
    
    with col3:
        if st.button("Task Phase"):
            st.session_state.current_page = "task"
            st.rerun()
    
    with col4:
        if st.button("Feedback", disabled=not st.session_state.get('tasks_completed', False)):
            st.session_state.current_page = "feedback"
            st.rerun() 