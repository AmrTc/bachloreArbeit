# Assessment Fields Documentation

## Overview
The Data Assistant Project now requires specific assessment fields to be filled for all users. These fields are essential for providing personalized cognitive load assessments and explanations.

## Required Assessment Fields

### 1. Age (`age`)
- **Type**: Integer
- **Required**: Yes
- **Default Value**: 25
- **Description**: User's age in years
- **Usage**: Used for cognitive load assessment and personalized explanations

### 2. Gender (`gender`)
- **Type**: String
- **Required**: Yes
- **Default Value**: "Not specified"
- **Description**: User's gender identity
- **Usage**: Used for demographic analysis and personalized content

### 3. Profession (`profession`)
- **Type**: String
- **Required**: Yes
- **Default Value**: "Student"
- **Description**: User's current profession or occupation
- **Usage**: Used for context-aware explanations and cognitive load assessment

### 4. Education Level (`education_level`)
- **Type**: String
- **Required**: Yes
- **Default Value**: "Bachelor"
- **Description**: User's highest level of education
- **Usage**: Used for determining explanation complexity and cognitive load capacity

## Implementation Details

### UserProfile Class
The `UserProfile` class in `clt_cft_agent.py` has been updated to include these fields as required parameters:

```python
@dataclass
class UserProfile:
    """User cognitive profile based on CLT assessments"""
    user_id: str
    sql_expertise_level: int
    cognitive_load_capacity: int
    sql_concept_levels: Dict[str, int]
    prior_query_history: List[Dict]
    learning_preferences: Dict[str, Any]
    last_updated: str
    
    # Required Assessment Fields
    age: int
    gender: str
    profession: str
    education_level: str
```

### UserManager Updates
The `UserManager` class has been updated to support these fields:

- **CSV Headers**: Added age, gender, profession, and education_level
- **create_user()**: Now accepts these fields as parameters
- **get_user_profile()**: Returns these fields from CSV data
- **Test Users**: Updated with realistic assessment data

### Validation
The system automatically validates that all required fields are present:

- **Missing Fields**: Automatically filled with default values
- **Logging**: Warnings are logged for missing fields
- **Auto-Save**: Profiles are automatically saved after validation

## Default Values

If any required field is missing, the system uses these defaults:

```python
age = 25
gender = "Not specified"
profession = "Student"
education_level = "Bachelor"
```

## Usage Examples

### Creating a User Profile
```python
from src.agents.clt_cft_agent import UserProfile

profile = UserProfile(
    user_id="john_doe",
    sql_expertise_level=3,
    cognitive_load_capacity=3,
    sql_concept_levels={...},
    prior_query_history=[],
    learning_preferences={...},
    last_updated="2024-01-01T00:00:00",
    # Required Assessment Fields
    age=28,
    gender="Male",
    profession="Data Analyst",
    education_level="Master"
)
```

### Updating Assessment Fields
```python
agent.update_user_assessment_fields(
    user_id="john_doe",
    age=29,
    gender="Male",
    profession="Senior Data Analyst",
    education_level="Master"
)
```

## Database Integration

The assessment fields are also integrated with the database models:

- **User Model**: Includes age, gender, profession, and education_level
- **CSV Storage**: UserManager stores these fields in CSV format
- **JSON Storage**: CLT-CFT Agent stores these fields in JSON format

## Benefits

### 1. Personalized Explanations
- Age-appropriate language complexity
- Profession-specific examples
- Education-level-appropriate technical depth

### 2. Cognitive Load Assessment
- Age-based cognitive capacity estimation
- Profession-based domain knowledge assessment
- Education-based learning preference inference

### 3. Research and Analytics
- Demographic analysis of user base
- Performance correlation studies
- Personalized learning path optimization

## Migration Notes

### Existing Users
- Users without assessment fields will automatically receive default values
- No data loss occurs during migration
- All existing functionality remains intact

### CSV Files
- Existing CSV files will be automatically updated with new headers
- Missing fields will be filled with default values
- Backward compatibility is maintained

## Future Enhancements

### 1. Additional Fields
- Study/training background
- Work experience years
- Preferred learning style

### 2. Validation Rules
- Age range validation (e.g., 13-100)
- Gender options validation
- Profession categorization
- Education level standardization

### 3. Dynamic Defaults
- Age-based profession suggestions
- Education-based profession mapping
- Cultural context considerations
