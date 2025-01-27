from google.api_core.exceptions import NotFound


def get_table_schema(client, project_id, dataset_id, table_id):
    """Generates schema string in the specified format."""
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    try:
        table = client.get_table(table_ref)
        schema_lines = [table_ref]  # Start with table reference
        
        # Process each field recursively
        for field in table.schema:
            schema_lines.extend(field_to_string(field))
            
        return '\n'.join(schema_lines)
        
    except NotFound:
        print(f"Table {table_ref} not found")
        return None

def field_to_string(field, parent=""):
    """Recursively converts fields to formatted strings with nested handling."""
    lines = []
    # Current field line
    full_name = f"{parent}{field.name}"
    line = f"\t - {full_name} ({field.field_type}): {field.description or ''}".strip()
    lines.append(line)
    
    # Process nested fields
    if field.fields:
        for sub_field in field.fields:
            lines.extend(field_to_string(sub_field, parent=f"{full_name}."))
    
    return lines
