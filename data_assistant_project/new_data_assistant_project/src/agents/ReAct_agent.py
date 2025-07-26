import sqlite3
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from anthropic import Anthropic
import logging
import os
from pathlib import Path

# Import modules using the installed package
from new_data_assistant_project.src.utils.my_config import MyConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Structure for query execution results"""
    success: bool
    data: Optional[pd.DataFrame]
    sql_query: str
    error_message: Optional[str]
    execution_time: float
    complexity_score: int  # 1-5 scale for CLT & CFT Agent

class ReActAgent:
    """
    LLM-based ReAct Agent for SQL execution and database operations.
    Follows ReAct (Reasoning and Acting) paradigm for natural language to SQL conversion.
    """
    
    def __init__(self, database_path: str = "new_data_assistant_project/src/database/superstore.db"):
        """
        Initialize ReAct Agent with database connection and API client.
        
        Args:
            database_path: Path to SQLite database
        """
        try:
            config = MyConfig()
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("No API key found in configuration")
            self.client = Anthropic(api_key=api_key)
            logger.info("Successfully initialized Anthropic client")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

        self.database_path = database_path
        self.model = "claude-sonnet-4-20250514"  # Using latest available Sonnet model
        
        # Initialize database schema cache
        self.schema_info = self._get_database_schema()
        
        # Query complexity patterns for cognitive load assessment
        self.complexity_patterns = {
            1: ['SELECT', 'simple'],  # Basic queries
            2: ['WHERE', 'GROUP BY', 'ORDER BY'],  # Filtering and grouping
            3: ['JOIN', 'INNER JOIN', 'LEFT JOIN'],  # Simple joins
            4: ['SUBQUERY', 'HAVING', 'CASE WHEN'],  # Complex logic
            5: ['WINDOW FUNCTION', 'CTE', 'MULTIPLE JOINS']  # Advanced operations
        }
    
    def _get_database_schema(self) -> str:
        """Extract database schema information for context."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                schema_info = "Database Schema:\n"
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    schema_info += f"\nTable: {table_name}\n"
                    for col in columns:
                        schema_info += f"  - {col[1]} ({col[2]})\n"
                
                return schema_info
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return "Schema information unavailable"
    
    def _assess_query_complexity(self, sql_query: str) -> int:
        """
        Assess SQL query complexity for CLT & CFT Agent.
        Returns complexity score 1-5 based on SQL features.
        """
        sql_upper = sql_query.upper()
        complexity_score = 1
        
        for level, patterns in self.complexity_patterns.items():
            for pattern in patterns:
                if pattern in sql_upper:
                    complexity_score = max(complexity_score, level)
        
        # Additional complexity factors
        if sql_upper.count('SELECT') > 1:  # Subqueries
            complexity_score = max(complexity_score, 4)
        
        if sql_upper.count('JOIN') > 1:  # Multiple joins
            complexity_score = max(complexity_score, 5)
        
        return min(complexity_score, 5)
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """
        Comprehensive SQL query cleaning to remove markdown formatting and fix SQLite compatibility.
        """
        # Remove markdown code blocks
        sql_query = re.sub(r'```sql\s*', '', sql_query, flags=re.MULTILINE | re.IGNORECASE)
        sql_query = re.sub(r'\s*```', '', sql_query, flags=re.MULTILINE)
        
        # Remove Anthropic API type annotations that may have leaked through
        sql_query = re.sub(r"', type='text'\)", '', sql_query)
        sql_query = re.sub(r"type='text'", '', sql_query)
        
        # Remove standalone 'sql' lines
        sql_query = re.sub(r'^\s*sql\s*$', '', sql_query, flags=re.MULTILINE | re.IGNORECASE)
        sql_query = re.sub(r'^\s*sql\s*\n', '', sql_query, flags=re.MULTILINE | re.IGNORECASE)
        
        # Find the actual SQL statement (starts with SELECT, INSERT, UPDATE, DELETE, WITH, etc.)
        lines = sql_query.split('\n')
        sql_lines = []
        found_sql_start = False
        
        for line in lines:
            line_stripped = line.strip().upper()
            
            # Start collecting lines when we find a SQL statement
            if not found_sql_start and any(line_stripped.startswith(keyword) for keyword in 
                                         ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'DROP', 'ALTER']):
                found_sql_start = True
                sql_lines.append(line)
            elif found_sql_start:
                # Stop collecting if we hit explanatory text
                if (line.strip() and 
                    not line_stripped.startswith(('FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'UNION', 'AND', 'OR', 'ON', 'AS', 'IN', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', ')', '(', ',')) and
                    not re.match(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*[,\)]', line) and  # Column names
                    not re.match(r'^\s*\d+', line) and  # Numbers
                    not re.match(r'^\s*[\'"]', line) and  # String literals
                    not re.match(r'^\s*[-+*/=<>!]', line) and  # Operators
                    ('This query' in line or 'provides' in line or 'shows' in line or 'The results' in line)):
                    break
                sql_lines.append(line)
        
        if sql_lines:
            sql_query = '\n'.join(sql_lines)
        
        # Final cleanup
        sql_query = sql_query.strip()
        
        # Remove any remaining trailing quotes or artifacts
        if sql_query.endswith("'"):
            sql_query = sql_query[:-1]
        
        # Remove leading/trailing whitespace and newlines
        sql_query = sql_query.strip('\n\r\t ')
        
        # Keep double quotes as they work in SQLite - no need to change them
        # The issue was in content extraction, not the SQL itself
        
        return sql_query
    
    def _generate_sql_with_reasoning(self, user_query: str) -> Tuple[str, str]:
        """
        Generate SQL query using ReAct reasoning pattern.
        Returns both the SQL query and the reasoning process.
        """
        system_prompt = f"""You are an expert SQL analyst following the ReAct (Reasoning and Acting) approach.
        
        {self.schema_info}
        
        For the given natural language query, follow this ReAct pattern:
        1. THOUGHT: Analyze what the user is asking for
        2. ACTION: Determine what SQL operations are needed
        3. OBSERVATION: Consider the database schema and constraints
        4. THOUGHT: Plan the SQL query structure
        5. ACTION: Write the final SQL query
        
        Provide both your reasoning process and the final SQL query.
        Be precise and consider performance implications.
        
        Format your response as:
        REASONING:
        [Your step-by-step reasoning]
        
        SQL:
        [Your SQL query]"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Generate SQL for: {user_query}"
                }]
            )
            
            # Extract content from the response properly for TextBlock objects
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
                else:
                    content += str(block)
            
            # Content successfully extracted from API
            
            # Extract reasoning and SQL
            if "REASONING:" in content and "SQL:" in content:
                parts = content.split("SQL:")
                reasoning = parts[0].replace("REASONING:", "").strip()
                sql_query = parts[1].strip()
                
                # Clean SQL query comprehensively
                sql_query = self._clean_sql_query(sql_query)
                
                return sql_query, reasoning
            else:
                # Fallback if format is not followed - try to extract SQL anyway
                cleaned_content = self._clean_sql_query(content)
                return cleaned_content, "Reasoning not available"
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return "", f"Error: {str(e)}"
    
    def execute_query(self, user_query: str) -> QueryResult:
        """
        Main method to process natural language query using ReAct approach.
        
        Args:
            user_query: Natural language data analysis request
            
        Returns:
            QueryResult with execution results and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Generate SQL using ReAct reasoning
            sql_query, reasoning = self._generate_sql_with_reasoning(user_query)
            
            if not sql_query:
                return QueryResult(
                    success=False,
                    data=None,
                    sql_query="",
                    error_message="Failed to generate SQL query",
                    execution_time=time.time() - start_time,
                    complexity_score=1
                )
            
            # Step 2: Assess query complexity for CLT & CFT Agent
            complexity_score = self._assess_query_complexity(sql_query)
            
            # Step 3: Execute SQL query
            with sqlite3.connect(self.database_path) as conn:
                try:
                    # Execute query and get results
                    result_df = pd.read_sql_query(sql_query, conn)
                    
                    execution_time = time.time() - start_time
                    
                    logger.info(f"Query executed successfully. Complexity: {complexity_score}")
                    logger.info(f"Reasoning: {reasoning[:100]}...")
                    
                    return QueryResult(
                        success=True,
                        data=result_df,
                        sql_query=sql_query,
                        error_message=None,
                        execution_time=execution_time,
                        complexity_score=complexity_score
                    )
                    
                except sqlite3.Error as e:
                    return QueryResult(
                        success=False,
                        data=None,
                        sql_query=sql_query,
                        error_message=f"SQL execution error: {str(e)}",
                        execution_time=time.time() - start_time,
                        complexity_score=complexity_score
                    )
                    
        except Exception as e:
            return QueryResult(
                success=False,
                data=None,
                sql_query="",
                error_message=f"Processing error: {str(e)}",
                execution_time=time.time() - start_time,
                complexity_score=1
            )
    
    def get_reasoning_explanation(self, sql_query: str, user_query: str) -> str:
        """
        Generate detailed reasoning explanation for the SQL query using Claude's extended thinking.
        """
        system_prompt = (
            "You are an expert SQL educator. "
            "Explain the given SQL query step by step using extended thinking. "
            "Show your reasoning as thinking blocks, so the user can follow your logic."
        )

        user_prompt = (
            f"Original question: {user_query}\n\n"
            f"SQL Query to explain:\n{sql_query}\n\n"
            "Please explain the SQL query step by step. "
            "Think out loud and show your reasoning as thinking blocks."
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            # Sammle alle Thinking/Text-Blöcke
            explanation = ""
            for block in response.content:
                explanation += str(block) + "\n\n"

            return explanation.strip() if explanation else "No reasoning blocks found."

        except Exception as e:
            logger.error(f"Error generating extended thinking explanation: {e}")
            return "Explanation unavailable due to error."
    
    def validate_sql_syntax(self, sql_query: str) -> Tuple[bool, str]:
        """Validate SQL syntax without execution."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"EXPLAIN QUERY PLAN {sql_query}")
                return True, "Valid SQL syntax"
        except sqlite3.Error as e:
            return False, f"Invalid SQL syntax: {str(e)}"
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample data from a table for context."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                return pd.read_sql_query(query, conn)
        except Exception as e:
            logger.error(f"Error getting sample data: {e}")
            return pd.DataFrame()

# Example usage and testing
if __name__ == "__main__":
    try:
        # Test API key loading
        config = MyConfig()
        api_key = config.get_api_key()
        print("\nAPI Key Test:")
        print(f"API Key loaded: {'Yes' if api_key else 'No'}")
        print(f"API Key value: {api_key}")
        
        # Initialize ReAct Agent
        react_agent = ReActAgent()
        print("\nReAct Agent Initialization:")
        print("Agent initialized successfully")
        
        # Example queries for testing
        test_queries = [
            "What are the top 5 products by sales?",
            "Show me sales by region and category",
            "Which customers have the highest profit margins?",
            "Compare sales performance across different time periods"
        ]
        
        for query in test_queries:
            print(f"\nProcessing: {query}")
            result = react_agent.execute_query(query)
            
            if result.success:
                print(f"SQL Generated: {result.sql_query}")
                print(f"Complexity Score: {result.complexity_score}")
                if result.data is not None:
                    print(f"Results shape: {result.data.shape}")
                else:
                    print("No data returned.")
                print(f"Execution time: {result.execution_time:.2f}s")
            else:
                print(f"Error: {result.error_message}")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")