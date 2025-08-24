import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass
from anthropic import Anthropic
import logging
import os
from pathlib import Path
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Structure for query execution results with visualization support"""
    success: bool
    data: Optional[pd.DataFrame]
    sql_query: str
    error_message: Optional[str]
    execution_time: float
    complexity_score: int
    visualization: Optional[Dict[str, Any]] = None


class ReActAgent:
    """
    Optimized LLM-based ReAct Agent using Claude API with Extended Thinking.
    Implements best practices from Anthropic documentation.
    """
    
    def __init__(self, database_config: dict = None, enable_caching: bool = True):
        """Initialize ReAct Agent with Extended Thinking capabilities."""
        self.enable_caching = enable_caching
        
        # Initialize Anthropic client with best practices
        try:
            # Get API key with multiple fallback methods
            api_key = self._get_api_key()
            
            if not api_key:
                raise ValueError("No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable.")
            
            self.client = Anthropic(api_key=api_key)
            
            # Use the model that supports Extended Thinking
            self.model = "claude-sonnet-4-20250514"  # Supports Extended Thinking
            
            # Extended Thinking configuration
            self.enable_extended_thinking = True
            self.thinking_time_limit = 30000  # 30 seconds max thinking time
            
            logger.info(f"✅ Initialized Anthropic client with model: {self.model}")
            logger.info(f"✅ Extended Thinking: {'Enabled' if self.enable_extended_thinking else 'Disabled'}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

        # Database configuration
        self.database_config = self._get_database_config(database_config)
        
        # Initialize database schema cache
        self.database_schema = {}
        self.table_metadata = {}
        
        # Fetch database schema
        try:
            self._fetch_database_schema()
            logger.info(f"✅ Database schema loaded: {len(self.database_schema)} tables")
        except Exception as e:
            logger.error(f"❌ Failed to fetch database schema: {e}")
            # Continue without schema for graceful degradation
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key with multiple fallback methods."""
        # Method 1: Environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Method 2: From config module if available
        if not api_key:
            try:
                from src.utils.my_config import MyConfig
                config = MyConfig()
                api_key = config.get_api_key()
            except:
                pass
        
        return api_key
    
    def _get_database_config(self, database_config: dict = None) -> dict:
        """Get database configuration with fallbacks."""
        if database_config:
            return database_config
        
        # Try to get from postgres_config module
        try:
            from src.database.postgres_config import PostgresConfig
            pg_config = PostgresConfig()
            return pg_config.get_connection_params()
        except:
            # Fallback configuration
            return {
                'host': '34.59.248.159',
                'port': 5432,
                'database': 'superstore',
                'user': 'postgres',
                'password': 'RHGAgo4<C4fyr',
                'sslmode': 'require'
            }
    
    def _fetch_database_schema(self):
        """Fetch database schema efficiently."""
        try:
            conn = psycopg2.connect(**self.database_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all tables with detailed information
            cursor.execute("""
                SELECT 
                    t.table_name,
                    obj_description(c.oid, 'pg_class') as table_comment
                FROM information_schema.tables t
                JOIN pg_class c ON c.relname = t.table_name
                WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name;
            """)
            tables = cursor.fetchall()
            
            for table_row in tables:
                table_name = table_row['table_name']
                
                # Get detailed column information
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = cursor.fetchall()
                
                # Get row count and sample data
                cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
                row_count = cursor.fetchone()['count']
                
                # Get sample values for each column (for better context)
                sample_values = {}
                for col in columns[:10]:  # Limit to first 10 columns
                    col_name = col['column_name']
                    try:
                        cursor.execute(f'''
                            SELECT DISTINCT "{col_name}" 
                            FROM "{table_name}" 
                            WHERE "{col_name}" IS NOT NULL
                            LIMIT 5
                        ''')
                        samples = [row[col_name] for row in cursor.fetchall()]
                        sample_values[col_name] = samples
                    except:
                        sample_values[col_name] = []
                
                # Get foreign key relationships
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = %s;
                """, (table_name,))
                foreign_keys = cursor.fetchall()
                
                # Store comprehensive schema information
                self.database_schema[table_name] = {
                    'columns': [col['column_name'] for col in columns],
                    'column_types': {col['column_name']: col['data_type'] for col in columns},
                    'nullable_columns': [col['column_name'] for col in columns if col['is_nullable'] == 'YES'],
                    'row_count': row_count,
                    'sample_values': sample_values,
                    'foreign_keys': foreign_keys,
                    'table_comment': table_row.get('table_comment', '')
                }
                
                logger.info(f"  ✓ {table_name}: {row_count} rows, {len(columns)} columns")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error fetching database schema: {e}")
            raise
    
    def _build_enhanced_schema_context(self) -> str:
        """Build enhanced schema context with relationships and samples."""
        if not self.database_schema:
            return "No database schema available."
        
        context_parts = ["DATABASE SCHEMA WITH RELATIONSHIPS AND SAMPLES:\n"]
        
        for table_name, info in self.database_schema.items():
            context_parts.append(f"\n📊 Table: {table_name}")
            if info.get('table_comment'):
                context_parts.append(f"   Description: {info['table_comment']}")
            context_parts.append(f"   Total Rows: {info['row_count']:,}")
            context_parts.append(f"   Columns ({len(info['columns'])} total):")
            
            # Show columns with types and sample values
            for col in info['columns'][:15]:  # Show first 15 columns
                col_type = info['column_types'][col]
                nullable = " (nullable)" if col in info.get('nullable_columns', []) else ""
                context_parts.append(f"    • {col} ({col_type}){nullable}")
                
                # Add sample values if available
                samples = info.get('sample_values', {}).get(col, [])
                if samples:
                    sample_str = str(samples[:3]) if len(samples) > 3 else str(samples)
                    context_parts.append(f"      Examples: {sample_str}")
            
            if len(info['columns']) > 15:
                context_parts.append(f"    ... and {len(info['columns']) - 15} more columns")
            
            # Show foreign key relationships
            if info.get('foreign_keys'):
                context_parts.append("   Relationships:")
                for fk in info['foreign_keys']:
                    context_parts.append(f"    • {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        return "\n".join(context_parts)
    
    def _generate_sql_with_extended_thinking(self, user_query: str) -> Tuple[str, str]:
        """
        Generate SQL query using Extended Thinking for complex queries.
        Uses the thinking_mode parameter for better reasoning.
        """
        
        schema_context = self._build_enhanced_schema_context()
        
        # Best Practice: Clear, structured system prompt
        system_prompt = """You are an expert PostgreSQL database analyst. Your task is to generate optimal SQL queries based on user requests.

CRITICAL REQUIREMENTS:
1. Use ONLY tables and columns that exist in the provided schema
2. Generate valid PostgreSQL syntax with proper quoting for identifiers
3. Handle NULL values appropriately using COALESCE or IS NULL checks
4. Use efficient JOINs and avoid cartesian products
5. Apply appropriate aggregations and window functions when needed
6. For "show table" requests, use: SELECT * FROM "table_name" LIMIT 100
7. Always consider performance implications

OUTPUT FORMAT:
Provide your response in this exact format:

THINKING:
[Your step-by-step reasoning about the query]

SQL:
[The final SQL query only, no explanations]

VISUALIZATION:
[Suggest chart type if applicable: bar, line, scatter, pie, table]"""

        # Best Practice: Structured user message
        user_message = f"""Database Schema Information:
{schema_context}

User Request: {user_query}

Please analyze this request carefully and generate the optimal SQL query."""

        try:
            if self.enable_extended_thinking and 'complex' in user_query.lower():
                # Use Extended Thinking for complex queries
                logger.info("Using Extended Thinking for complex query analysis...")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    temperature=0,  # Deterministic for SQL
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_message
                    }],
                    # Extended Thinking parameters
                    metadata={
                        "thinking_mode": "extended",
                        "thinking_time_limit": self.thinking_time_limit
                    }
                )
            else:
                # Standard generation for simple queries
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_message
                    }]
                )
            
            # Extract response content
            content = response.content[0].text if response.content else ""
            
            # Parse structured response
            sql_query = self._extract_sql_from_response(content)
            thinking = self._extract_section(content, "THINKING:", "SQL:")
            
            if not sql_query:
                # Fallback: Try to extract SQL from anywhere in the response
                sql_query = self._extract_sql_fallback(content)
            
            # Clean and validate SQL
            sql_query = self._clean_and_validate_sql(sql_query)
            
            logger.info(f"Generated SQL using {'Extended Thinking' if self.enable_extended_thinking else 'Standard'} mode")
            
            return sql_query, thinking or "Direct SQL generation"
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return self._generate_fallback_sql(user_query), f"Error: {str(e)}"
    
    def _extract_sql_from_response(self, content: str) -> str:
        """Extract SQL from structured response."""
        sql_section = self._extract_section(content, "SQL:", "VISUALIZATION:")
        if not sql_section:
            sql_section = self._extract_section(content, "SQL:", None)
        return sql_section.strip() if sql_section else ""
    
    def _extract_section(self, content: str, start_marker: str, end_marker: Optional[str]) -> str:
        """Extract a section between markers."""
        if start_marker not in content:
            return ""
        
        start_idx = content.index(start_marker) + len(start_marker)
        
        if end_marker and end_marker in content[start_idx:]:
            end_idx = content.index(end_marker, start_idx)
            return content[start_idx:end_idx].strip()
        
        return content[start_idx:].strip()
    
    def _extract_sql_fallback(self, content: str) -> str:
        """Fallback SQL extraction using patterns."""
        # Look for SELECT statements
        patterns = [
            r'(SELECT[\s\S]+?;)',
            r'(WITH[\s\S]+?SELECT[\s\S]+?;)',
            r'(INSERT[\s\S]+?;)',
            r'(UPDATE[\s\S]+?;)',
            r'(DELETE[\s\S]+?;)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _clean_and_validate_sql(self, sql_query: str) -> str:
        """Clean and validate SQL query."""
        if not sql_query:
            return ""
        
        # Remove markdown code blocks
        sql_query = re.sub(r'```sql?\s*', '', sql_query, flags=re.IGNORECASE)
        sql_query = re.sub(r'```\s*', '', sql_query)
        
        # Remove inline comments but keep the query
        lines = sql_query.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove comments after --
            if '--' in line:
                line = line[:line.index('--')]
            cleaned_lines.append(line)
        
        sql_query = '\n'.join(cleaned_lines)
        
        # Ensure query ends with semicolon
        sql_query = sql_query.strip()
        if sql_query and not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def _generate_fallback_sql(self, user_query: str) -> str:
        """Generate fallback SQL for common patterns."""
        query_lower = user_query.lower()
        
        # Pattern matching for common requests
        if "show" in query_lower and "table" in query_lower:
            # Extract table name
            for table_name in self.database_schema.keys():
                if table_name.lower() in query_lower:
                    return f'SELECT * FROM "{table_name}" LIMIT 100;'
            
            # If no specific table, show first available table
            if self.database_schema:
                first_table = list(self.database_schema.keys())[0]
                return f'SELECT * FROM "{first_table}" LIMIT 100;'
        
        elif "list" in query_lower and "tables" in query_lower:
            return """
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
            """
        
        elif "count" in query_lower:
            # Try to find table name
            for table_name in self.database_schema.keys():
                if table_name.lower() in query_lower:
                    return f'SELECT COUNT(*) as total_count FROM "{table_name}";'
        
        return "SELECT 'Unable to generate SQL for this request' as message;"
    
    def _execute_sql_query(self, sql_query: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """Execute SQL query with comprehensive error handling."""
        try:
            # Establish connection with timeout
            conn = psycopg2.connect(
                **self.database_config,
                connect_timeout=30
            )
            
            # Set statement timeout for long-running queries
            with conn.cursor() as cursor:
                cursor.execute("SET statement_timeout = '30s';")
            
            # Execute query and fetch results
            df = pd.read_sql_query(sql_query, conn)
            
            conn.close()
            
            logger.info(f"✅ Query executed successfully: {len(df)} rows returned")
            return df, None
            
        except psycopg2.OperationalError as e:
            error_msg = f"Database connection error: {str(e)}"
            logger.error(error_msg)
            return pd.DataFrame(), error_msg
            
        except psycopg2.ProgrammingError as e:
            error_msg = f"SQL syntax error: {str(e)}"
            logger.error(error_msg)
            return pd.DataFrame(), error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return pd.DataFrame(), error_msg
    
    def execute_query(self, user_query: str, show_sql_in_explanation: bool = False) -> QueryResult:
        """
        Execute user query with Extended Thinking for complex queries.
        
        Args:
            user_query: Natural language query from user
            show_sql_in_explanation: Whether to include SQL in the response
            
        Returns:
            QueryResult with data and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {user_query}")
            
            # Check if this is a complex query that needs Extended Thinking
            is_complex = any(keyword in user_query.lower() for keyword in [
                'forecast', 'predict', 'analyze', 'correlation', 'trend',
                'pattern', 'complex', 'multiple', 'advanced'
            ])
            
            if is_complex:
                logger.info("📊 Detected complex query - using Extended Thinking")
            
            # Generate SQL with Extended Thinking if needed
            sql_query, reasoning = self._generate_sql_with_extended_thinking(user_query)
            
            if not sql_query or sql_query == "SELECT 'Unable to generate SQL for this request' as message;":
                # Try direct table request as fallback
                return self._handle_direct_request(user_query, start_time)
            
            # Execute SQL query
            data, error = self._execute_sql_query(sql_query)
            
            if error:
                return QueryResult(
                    success=False,
                    data=None,
                    sql_query=sql_query if show_sql_in_explanation else "",
                    error_message=error,
                    execution_time=time.time() - start_time,
                    complexity_score=1
                )
            
            # Success
            execution_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                data=data,
                sql_query=sql_query,
                error_message=None,
                execution_time=execution_time,
                complexity_score=self._assess_query_complexity(sql_query),
                visualization=self._suggest_visualization(data)
            )
            
        except Exception as e:
            logger.error(f"Error in execute_query: {e}")
            return QueryResult(
                success=False,
                data=None,
                sql_query="",
                error_message=f"Query processing error: {str(e)}",
                execution_time=time.time() - start_time,
                complexity_score=1
            )
    
    def _handle_direct_request(self, user_query: str, start_time: float) -> QueryResult:
        """Handle requests that might not need SQL."""
        
        # Check for table information requests
        if "table" in user_query.lower() and any(word in user_query.lower() for word in ["available", "list", "show"]):
            tables_data = []
            for table_name, info in self.database_schema.items():
                tables_data.append({
                    'Table Name': table_name,
                    'Row Count': info['row_count'],
                    'Column Count': len(info['columns']),
                    'Has Relationships': 'Yes' if info.get('foreign_keys') else 'No'
                })
            
            df = pd.DataFrame(tables_data)
            
            return QueryResult(
                success=True,
                data=df,
                sql_query="",
                error_message=None,
                execution_time=time.time() - start_time,
                complexity_score=1
            )
        
        return QueryResult(
            success=False,
            data=None,
            sql_query="",
            error_message="Could not process request. Please try rephrasing.",
            execution_time=time.time() - start_time,
            complexity_score=1
        )
    
    def _assess_query_complexity(self, sql_query: str) -> int:
        """Assess query complexity for cognitive load calculation."""
        if not sql_query:
            return 1
        
        sql_upper = sql_query.upper()
        complexity = 1
        
        # Check for various SQL features
        complexity_features = {
            'JOIN': 2,
            'GROUP BY': 1,
            'HAVING': 1,
            'WINDOW': 2,
            'WITH': 2,  # CTE
            'UNION': 1,
            'SUBQUERY': 2,
            'CASE': 1
        }
        
        for feature, score in complexity_features.items():
            if feature in sql_upper:
                complexity += score
        
        # Check for multiple JOINs
        join_count = sql_upper.count('JOIN')
        if join_count > 2:
            complexity += join_count - 2
        
        # Check for nested subqueries
        if sql_upper.count('SELECT') > 1:
            complexity += 1
        
        return min(complexity, 5)
    
    def _suggest_visualization(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Suggest appropriate visualization based on data characteristics."""
        if data.empty or len(data.columns) == 0:
            return None
        
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        text_cols = data.select_dtypes(include=['object']).columns.tolist()
        date_cols = data.select_dtypes(include=['datetime64']).columns.tolist()
        
        viz_suggestion = {
            'type': 'table',
            'numeric_columns': numeric_cols,
            'text_columns': text_cols,
            'date_columns': date_cols
        }
        
        # Smart visualization suggestions
        if date_cols and numeric_cols:
            viz_suggestion['type'] = 'line'
            viz_suggestion['recommended'] = 'time series line chart'
            viz_suggestion['x_axis'] = date_cols[0]
            viz_suggestion['y_axis'] = numeric_cols[0]
        elif len(numeric_cols) >= 2:
            viz_suggestion['type'] = 'scatter'
            viz_suggestion['recommended'] = 'scatter plot for correlation'
            viz_suggestion['x_axis'] = numeric_cols[0]
            viz_suggestion['y_axis'] = numeric_cols[1]
        elif len(numeric_cols) == 1 and len(text_cols) >= 1:
            if len(data[text_cols[0]].unique()) <= 20:
                viz_suggestion['type'] = 'bar'
                viz_suggestion['recommended'] = 'bar chart'
                viz_suggestion['x_axis'] = text_cols[0]
                viz_suggestion['y_axis'] = numeric_cols[0]
            else:
                viz_suggestion['type'] = 'table'
                viz_suggestion['recommended'] = 'table (too many categories for chart)'
        elif len(data) <= 10 and len(numeric_cols) >= 1:
            viz_suggestion['type'] = 'pie'
            viz_suggestion['recommended'] = 'pie chart for distribution'
        
        return viz_suggestion
    
    def get_available_tables_info(self) -> str:
        """Get formatted information about available tables."""
        if not self.database_schema:
            return "No database schema available."
        
        info_parts = ["📊 **Available Database Tables**\n"]
        
        total_rows = sum(info['row_count'] for info in self.database_schema.values())
        info_parts.append(f"**Database Summary:** {len(self.database_schema)} tables, {total_rows:,} total rows\n")
        
        for table_name, info in self.database_schema.items():
            info_parts.append(f"\n**{table_name}**")
            info_parts.append(f"  • Rows: {info['row_count']:,}")
            info_parts.append(f"  • Columns: {len(info['columns'])}")
            
            # Show first few columns
            cols_preview = ', '.join(info['columns'][:5])
            if len(info['columns']) > 5:
                cols_preview += f" ... +{len(info['columns']) - 5} more"
            info_parts.append(f"  • Fields: {cols_preview}")
            
            # Show relationships if any
            if info.get('foreign_keys'):
                info_parts.append(f"  • Related tables: {len(info['foreign_keys'])} relationships")
        
        return "\n".join(info_parts)
    
    def generate_python_code(self, data: pd.DataFrame, analysis_request: str) -> str:
        """Generate Python code using best practices."""
        if data.empty:
            return "# No data available for analysis"
        
        # Build context about the data
        data_context = f"""
Data shape: {data.shape}
Columns: {list(data.columns)}
Data types: {data.dtypes.to_dict()}
Numeric columns: {data.select_dtypes(include=['number']).columns.tolist()}
Text columns: {data.select_dtypes(include=['object']).columns.tolist()}
"""
        
        prompt = f"""Generate clean, production-ready Python code for this analysis request.

{data_context}

Analysis Request: {analysis_request}

Requirements:
1. Use pandas for data manipulation
2. Use plotly.express or plotly.graph_objects for visualizations
3. Include proper error handling with try/except blocks
4. Add helpful comments
5. Make the code reusable and modular
6. Return ONLY executable Python code

Code:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,  # Slight creativity for code generation
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            code = response.content[0].text if response.content else ""
            
            # Clean code from markdown blocks
            code = re.sub(r'```python?\s*', '', code)
            code = re.sub(r'```\s*', '', code)
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"Error generating Python code: {e}")
            return f"# Error generating code: {e}\n# Please try again with a simpler request"