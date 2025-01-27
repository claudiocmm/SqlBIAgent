import re

def extract_only_sql_query(input_str: str) -> str: 
    sql_query = re.search(r'```sql(.*?)```', input_str, re.DOTALL)
    return sql_query.group(1)