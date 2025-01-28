import re

def extract_only_sql_query(input_str: str) -> str: 
    try:
        sql_query = re.search(r'```sql(.*?)```', input_str, re.DOTALL)
        output = sql_query.group(1)

    #sometimes the LLM forget to remove the backticks in the end
    except Exception:
        output = input_str.replace("```sql","")

    return output