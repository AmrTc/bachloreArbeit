import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from anthropic import Anthropic
import logging
import os
from pathlib import Path

# PostgreSQL imports
try:
    from new_data_assistant_project.src.utils.my_config import MyConfig
    from new_data_assistant_project.src.database.postgres_config import PostgresConfig
except ImportError:
    from src.utils.my_config import MyConfig
    from src.database.postgres_config import PostgresConfig

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
    LLM-based ReAct Agent for SQL execution and database operations using PostgreSQL.
    Follows ReAct (Reasoning and Acting) paradigm for natural language to SQL conversion.
    """
    
    def __init__(self, database_config: dict = None):
        """
        Initialize ReAct Agent with PostgreSQL connection and API client.
        
        Args:
            database_config: PostgreSQL connection configuration dictionary
        """
        # Initialize API client with better error handling
        try:
            config = MyConfig()
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("No API key found in configuration")
            
            # Validate API key format
            if not api_key.startswith('sk-ant-'):
                logger.warning(f"API key format seems incorrect: {api_key[:10]}...")
            
            self.client = Anthropic(api_key=api_key)
            logger.info(f"Successfully initialized Anthropic client with key: {api_key[:10]}...")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

        # Use provided database config or get from MyConfig
        if database_config:
            self.database_config = database_config
        else:
            self.database_config = config.get_postgres_config()
        
        # Log database config (without password)
        safe_config = {k: v for k, v in self.database_config.items() if k != 'password'}
        safe_config['password'] = '***' if 'password' in self.database_config else 'None'
        logger.info(f"Database config: {safe_config}")
        
        self.model = "claude-sonnet-4-20250514"  # Using latest available Sonnet model
        
        # Initialize database schema cache with fallback
        try:
            self.schema_info = self._get_database_schema()
            logger.info(f"Schema loaded successfully: {len(self.schema_info)} characters")
        except Exception as e:
            logger.error(f"Failed to load database schema: {e}")
            self.schema_info = self._get_fallback_schema()
        
        # Query complexity patterns for cognitive load assessment
        self.complexity_patterns = {
            1: ['SELECT', 'simple'],  # Basic queries
            2: ['WHERE', 'GROUP BY', 'ORDER BY'],  # Filtering and grouping
            3: ['JOIN', 'INNER JOIN', 'LEFT JOIN'],  # Simple joins
            4: ['SUBQUERY', 'HAVING', 'CASE WHEN'],  # Complex logic
            5: ['WINDOW FUNCTION', 'CTE', 'MULTIPLE JOINS']  # Advanced operations
        }
    
    def _get_fallback_schema(self) -> str:
        """Provide fallback schema information when database connection fails."""
        return """PostgreSQL Database Schema (Fallback - Superstore Sample):

Table: orders
  - row_id (integer) PRIMARY KEY
  - order_id (varchar) 
  - order_date (date)
  - ship_date (date)
  - ship_mode (varchar)
  - customer_id (varchar)
  - customer_name (varchar)
  - segment (varchar)
  - country (varchar)
  - city (varchar)
  - state (varchar)
  - postal_code (varchar)
  - region (varchar)
  - product_id (varchar)
  - category (varchar)
  - sub_category (varchar)
  - product_name (varchar)
  - sales (numeric)
  - quantity (integer)
  - discount (numeric)
  - profit (numeric)
  Total rows: ~10000

This is a sample retail/superstore dataset with order information, customer details, and sales metrics."""
    
    def _get_database_schema(self) -> str:
        """Extract PostgreSQL database schema information for context."""
        try:
            import psycopg2
            
            # Test connection first
            logger.info("Testing PostgreSQL connection...")
            conn = psycopg2.connect(**self.database_config)
            logger.info("PostgreSQL connection successful")
            
            cursor = conn.cursor()
            
            # Show all available tables
            schema_info = "PostgreSQL Database Schema (All tables available):\n"
            
            # Get all table names
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            logger.info(f"Found {len(tables)} tables in database")
            
            for table in tables:
                table_name = table[0]
                schema_info += f"\nTable: {table_name}\n"
                
                # Get table info
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = cursor.fetchall()
                
                for col in columns:
                    schema_info += f"  - {col[0]} ({col[1]})"
                    if col[2] == 'NO':
                        schema_info += " NOT NULL"
                    if col[3]:
                        schema_info += f" DEFAULT {col[3]}"
                    schema_info += "\n"
                
                # Add sample data info
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    schema_info += f"  Total rows: {row_count}\n"
                except Exception as e:
                    logger.warning(f"Could not count rows for {table_name}: {e}")
                    schema_info += f"  Could not count rows\n"
            
            cursor.close()
            conn.close()
            return schema_info
        except Exception as e:
            logger.error(f"Error getting PostgreSQL database schema: {e}")
            # Return fallback schema instead of empty string
            return self._get_fallback_schema()
    
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
        Comprehensive SQL query cleaning to remove markdown formatting and fix PostgreSQL compatibility.
        """
        if not sql_query or not isinstance(sql_query, str):
            return ""
        
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
        
        return sql_query
    
    def _generate_sql_with_reasoning(self, user_query: str) -> Tuple[str, str]:
        """
        Generate SQL query using ReAct reasoning pattern with improved error handling.
        Returns both the SQL query and the reasoning process.
        """
        system_prompt = f"""You are an expert SQL analyst following the ReAct (Reasoning and Acting) approach.
        
        {self.schema_info}
        
        IMPORTANT: All SQL operations are now allowed. You can generate any type of SQL query.
        
        For the given natural language query, follow this ReAct pattern:
        1. THOUGHT: Analyze what the user is asking for
        2. ACTION: Determine what SQL operations are needed
        3. OBSERVATION: Consider the database schema and available tables
        4. THOUGHT: Plan the SQL query structure
        5. ACTION: Write the final SQL query
        
        Provide both your reasoning process and the final SQL query.
        Be precise and consider performance implications.
        You can generate any SQL operation including SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, etc.
        
        Format your response as:
        REASONING:
        [Your step-by-step reasoning]
        
        SQL:
        [Your SQL query - MUST be valid PostgreSQL syntax]"""
        
        try:
            logger.info(f"Generating SQL for query: {user_query}")
            logger.info(f"Using model: {self.model}")
            
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
            
            logger.info(f"API response received: {len(content)} characters")
            logger.debug(f"Raw API response: {content[:500]}...")
            
            # Content successfully extracted from API
            
            # Extract reasoning and SQL
            if "REASONING:" in content and "SQL:" in content:
                parts = content.split("SQL:")
                reasoning = parts[0].replace("REASONING:", "").strip()
                sql_query = parts[1].strip()
                
                # Clean SQL query comprehensively
                sql_query = self._clean_sql_query(sql_query)
                
                logger.info(f"SQL query extracted: {sql_query[:100]}...")
                
                return sql_query, reasoning
            else:
                # Fallback if format is not followed - try to extract SQL anyway
                logger.warning("API response format not as expected, trying fallback extraction")
                cleaned_content = self._clean_sql_query(content)
                if cleaned_content:
                    logger.info(f"Fallback SQL extraction successful: {cleaned_content[:100]}...")
                    return cleaned_content, "Reasoning not available"
                else:
                    logger.error("No SQL query could be extracted from API response")
                    return "", "Could not extract SQL from response"
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            logger.exception("Full traceback:")
            return "", f"I encountered an error while processing your request: {str(e)}"
    
    def execute_query(self, user_query: str) -> QueryResult:
        """
        Main method to process natural language query using ReAct approach with PostgreSQL.
        
        Args:
            user_query: Natural language data analysis request
            
        Returns:
            QueryResult with execution results and metadata
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Starting query execution for: {user_query}")
            
            # Step 1: Generate SQL using ReAct reasoning
            sql_query, reasoning = self._generate_sql_with_reasoning(user_query)
            
            if not sql_query:
                logger.error("No SQL query generated")
                return QueryResult(
                    success=False,
                    data=None,
                    sql_query="",
                    error_message="I couldn't generate a SQL query for your request. This might be due to API connectivity issues or the request being unclear. Please try rephrasing your question.",
                    execution_time=time.time() - start_time,
                    complexity_score=1
                )
            
            # Step 2: SQL validation removed - all queries are now allowed
            # The agent only receives instructions and does not share user information
            
            # Step 3: Assess query complexity for CLT & CFT Agent
            complexity_score = self._assess_query_complexity(sql_query)
            logger.info(f"Query complexity score: {complexity_score}")
            
            # Step 4: Execute SQL query using PostgreSQL
            try:
                import psycopg2
                logger.info("Connecting to PostgreSQL for query execution")
                conn = psycopg2.connect(**self.database_config)
                
                # Execute query and get results
                logger.info(f"Executing SQL: {sql_query}")
                result_df = pd.read_sql_query(sql_query, conn)
                conn.close()
                
                execution_time = time.time() - start_time
                
                logger.info(f"Query executed successfully. Complexity: {complexity_score}, Rows: {len(result_df)}, Time: {execution_time:.2f}s")
                logger.info(f"Reasoning: {reasoning[:100]}...")
                
                return QueryResult(
                    success=True,
                    data=result_df,
                    sql_query=sql_query,
                    error_message=None,
                    execution_time=execution_time,
                    complexity_score=complexity_score
                )
                
            except psycopg2.Error as e:
                # Log the actual error for debugging but return user-friendly message
                logger.error(f"PostgreSQL execution error: {str(e)}")
                logger.error(f"Failed SQL query: {sql_query}")
                return QueryResult(
                    success=False,
                    data=None,
                    sql_query=sql_query,
                    error_message=f"I encountered a database error while executing the query. The query might have syntax issues or reference non-existent tables/columns. Error: {str(e)}",
                    execution_time=time.time() - start_time,
                    complexity_score=complexity_score
                )
                    
        except Exception as e:
            # Log the actual error for debugging but return user-friendly message
            logger.error(f"Processing error in ReAct agent: {str(e)}")
            logger.exception("Full traceback:")
            return QueryResult(
                success=False,
                data=None,
                sql_query="",
                error_message=f"I'm having trouble processing your request right now. Error details: {str(e)}. Please try again with a different question about the business data.",
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
        """Validate SQL syntax without execution using PostgreSQL."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.database_config)
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN {sql_query}")
            cursor.close()
            conn.close()
            return True, "Valid SQL syntax"
        except psycopg2.Error as e:
            return False, f"Invalid SQL syntax: {str(e)}"
    
    def get_sample_data(self, table_name: str = None, limit: int = 5) -> pd.DataFrame:
        """Get sample data from the specified table or list all available tables using PostgreSQL."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.database_config)
            
            if table_name:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                return pd.read_sql_query(query, conn)
            else:
                # List all available tables
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                table_names = [table[0] for table in tables]
                
                # Create a DataFrame with table information
                table_info = []
                for table in table_names:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        table_info.append({"table_name": table, "row_count": row_count})
                    except:
                        table_info.append({"table_name": table, "row_count": "Unknown"})
                
                cursor.close()
                conn.close()
                return pd.DataFrame(table_info)
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
        print(f"API Key value: {api_key[:10]}..." if api_key else "No API key found")
        
        # Initialize ReAct Agent with PostgreSQL
        react_agent = ReActAgent()
        print("\nReAct Agent Initialization:")
        print("Agent initialized successfully with PostgreSQL")
        
        # Test simple query
        test_query = "Show me the first 5 rows from any table"
        print(f"\nTesting query: {test_query}")
        result = react_agent.execute_query(test_query)
        
        if result.success:
            print(f"SQL Generated: {result.sql_query}")
            print(f"Complexity Score: {result.complexity_score}")
            if result.data is not None:
                print(f"Results shape: {result.data.shape}")
            print(f"Execution time: {result.execution_time:.2f}s")
        else:
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()