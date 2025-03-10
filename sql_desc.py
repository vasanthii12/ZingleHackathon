import os
from sqllineage.runner import LineageRunner
from sqlparse import parse, tokens as T
import pandas as pd
from typing import List, Dict
import google.generativeai as genai
import time
from google.api_core import retry
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = 20  
def extract_columns_from_sql(sql_file_path: str) -> List[Dict]:
    """Extract columns and their context from SQL queries using SQLLineage"""
    try:
        with open(sql_file_path, 'r') as f:
            sql = f.read()
        
        if not sql.strip():
            return []
        
        queries = [q.strip() for q in sql.split(';') if q.strip()]
        if not queries:
            return []
        
        all_columns = []
        for query in queries:
            try:
                query = ' '.join(query.split())
                runner = LineageRunner(query)
                
                # Clean table names
                target_tables = [str(t).replace('<default>.', '') for t in runner.target_tables]
                source_tables = [str(t).replace('<default>.', '') for t in runner.source_tables]
                
                # Handle CREATE TABLE AS statements
                if 'CREATE TABLE' in query.upper() and ' AS ' in query.upper():
                    create_parts = query.split(' AS ', 1)[0].split()
                    target_table = create_parts[create_parts.index('TABLE') + 1].strip()
                    target_table = target_table.replace('<default>.', '')
                    
                    select_part = query.split(' AS ', 1)[1]
                    parsed_select = parse(select_part)[0]
                    
                    for token in parsed_select.tokens:
                        if hasattr(token, 'tokens'):
                            for item in token.tokens:
                                if hasattr(item, 'value'):
                                    if item.value.upper() in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', ',', '(', ')']:
                                        continue
                                    
                                    if ' AS ' in item.value:
                                        col_parts = item.value.split(' AS ')
                                        col_name = col_parts[-1].strip()
                                        definition = item.value.strip()
                                    else:
                                        col_name = item.value.strip()
                                        definition = item.value.strip()
                                    
                                    col_name = col_name.strip('"\'`')
                                    if col_name and not col_name.isdigit():
                                        all_columns.append({
                                            'table': target_table,
                                            'column': col_name,
                                            'full_query': query,
                                            'definition': definition,
                                            'source_tables': source_tables
                                        })
                
                # Handle regular CREATE TABLE statements
                elif query.upper().strip().startswith('CREATE TABLE') and '(' in query:
                    table_name = target_tables[0] if target_tables else None
                    if table_name:
                        start_idx = query.find('(')
                        end_idx = query.rfind(')')
                        if start_idx != -1 and end_idx != -1:
                            column_text = query[start_idx + 1:end_idx]
                            column_defs = []
                            current_def = []
                            paren_count = 0
                            
                            for char in column_text:
                                if char == '(':
                                    paren_count += 1
                                elif char == ')':
                                    paren_count -= 1
                                elif char == ',' and paren_count == 0:
                                    column_defs.append(''.join(current_def).strip())
                                    current_def = []
                                    continue
                                current_def.append(char)
                            
                            if current_def:
                                column_defs.append(''.join(current_def).strip())
                            
                            for col_def in column_defs:
                                if col_def and not any(keyword in col_def.upper().split()[0] for keyword in ['PRIMARY', 'FOREIGN', 'CONSTRAINT']):
                                    col_name = col_def.split()[0].strip('"\'`')
                                    all_columns.append({
                                        'table': table_name,
                                        'column': col_name,
                                        'full_query': query,
                                        'definition': col_def,
                                        'source_tables': source_tables
                                    })
            except Exception:
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_columns = []
        for col in all_columns:
            key = (col['table'].replace('<default>.', ''), col['column'])
            if key not in seen:
                seen.add(key)
                col['table'] = col['table'].replace('<default>.', '')
                unique_columns.append(col)
        
        return unique_columns
        
    except Exception:
        return []

def generate_column_description(column_info: Dict, model, max_retries=3, initial_delay=1) -> str:
    """Generate column description using Google's Gemini API with retry logic"""
    definition = f"Definition: {column_info['definition']}" if column_info['definition'] else ""
    
    prompt = f"""
    Generate a precise and detailed description for the following SQL column:
    
    Table: {column_info['table']}
    Column: {column_info['column']}
    {definition}
    Source Tables: {', '.join(column_info['source_tables'])}
    
    Query Context:
    {column_info['full_query']}
    
    Format the description as follows:
    **`{column_info['table']}.{column_info['column']}:`** <description>
    
    The description should include:
    1. The purpose and meaning of this column
    2. How it's calculated (if derived)
    3. Any business logic or conditions applied
    4. Data relationships with source tables
    5. Data type constraints and validations (if any)
    
    Keep the description technical but understandable.
    """
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except ResourceExhausted:
            if attempt == max_retries - 1:
                return f"**`{column_info['table']}.{column_info['column']}:`** Description generation failed due to API rate limits"
            wait_time = initial_delay * (2 ** attempt)
            time.sleep(wait_time)
        except Exception as e:
            return f"**`{column_info['table']}.{column_info['column']}:`** Description generation failed: {str(e)}"

def main():
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    sql_file_path = "queries.sql"
    
    if not os.path.exists(sql_file_path) or os.path.getsize(sql_file_path) == 0:
        print("Error: SQL file not found or empty")
        return
    
    columns = extract_columns_from_sql(sql_file_path)
    if not columns:
        print("No columns were extracted from the SQL file")
        return
    
    results = []
    for i, col in enumerate(columns, 1):
        if i > 1:
            time.sleep(1)
        description = generate_column_description(col, model)
        results.append({
            'Table': col['table'],
            'Column': col['column'],
            'Description': description
        })
    
    df = pd.DataFrame(results)
    df.to_excel('column_descriptions.xlsx', index=False)
    print("Descriptions for SQL queries generated Successfully")

    # Generate report
    total_queries = len(set(col['full_query'] for col in columns))
    report = f"""Column Description Generation Report
    
Total SQL Queries Processed: {total_queries}
Total Columns Documented: {len(columns)}

Process Summary:
1. SQL queries were parsed using SQLLineage to extract column-level lineage
2. For each column, context was gathered including source tables and full query
3. Google's Gemini Pro model was used to generate detailed descriptions based on the context
4. Results were compiled into an Excel spreadsheet

The generated descriptions include:
- Column purpose and meaning
- Calculation methods for derived columns
- Business logic and conditions
- Data relationships with source tables
"""
    
    with open('generation_report.txt', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main()