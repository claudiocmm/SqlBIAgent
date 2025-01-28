from google.api_core.exceptions import NotFound
from google.cloud import bigquery
import pandas as pd
import json

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


def create_table_from_json_schema(project_id, dataset_id, table_id, json_schema_path):
    # Initialize the BigQuery client
    client = bigquery.Client(project=project_id)

    # Load the JSON schema file
    with open(json_schema_path, "r") as schema_file:
        schema_json = json.load(schema_file)

    # Convert JSON schema to BigQuery SchemaField objects
    schema = []
    for field in schema_json:
        schema.append(
            bigquery.SchemaField(
                name=field["name"],
                field_type=field["type"],
                mode=field.get("mode", "NULLABLE"),  # Default to NULLABLE if not specified
                description=field.get("description", ""),  # Use empty string if no description
            )
        )

    # Create table reference
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    # Create Table object
    table = bigquery.Table(table_ref, schema=schema)

    # Create the table in BigQuery
    try:
        table = client.create_table(table)  # API request
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise

    return table


def generate_schema_from_dataframe(df: pd.DataFrame, output_path: str, descriptions: str =None, modes: str =None):
    """
    Generate a BigQuery schema JSON file from DataFrame columns and data types.
    
    Args:
        df: pandas DataFrame
        output_path: Path to save the schema JSON file

    Returns:
        Dictionary representation of the schema
    """
    # Default values for optional parameters
    descriptions = descriptions or {}
    modes = modes or {}
    
    # Type mapping from pandas dtypes to BigQuery types
    type_mapping = {
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'object': 'STRING',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'DATETIME',
        'timedelta64[ns]': 'STRING',
        'category': 'STRING',
        'string': 'STRING',
        'UInt32': 'INTEGER',
        'Int32': 'INTEGER'
    }

    schema = []
    for column in df.columns:
        dtype = str(df[column].dtype)
        field = {
            "name": column,
            "type": type_mapping.get(dtype, 'STRING'),  # Default to STRING for unmapped types
            "mode": modes.get(column, 'NULLABLE'),      # Default to NULLABLE
            "description": descriptions.get(column, '') # Default to empty string
        }
        schema.append(field)

    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)
        
    return schema

def convert_schema_json_to_bq_schemafield(schema_json):
    """Recursively build BigQuery schema with nested fields"""
    schema = []
    for field in schema_json:
        subschema = []
        if 'fields' in field:
            subschema = convert_schema_json_to_bq_schemafield(field['fields'])
        schema_field = bigquery.SchemaField(
            name=field['name'],
            field_type=field['type'],
            mode=field.get('mode', 'NULLABLE'),
            description=field.get('description', ''),
            fields=subschema
        )
        schema.append(schema_field)
    return schema


def csv_to_bigquery(project_id, dataset_id, table_id, csv_path, schema_path, 
                    write_disposition='WRITE_TRUNCATE', autodetect=False):
    """
    Upload CSV data to BigQuery with schema validation
    
    Args:
        project_id: GCP project ID
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        csv_path: Path to CSV file
        schema_path: Path to JSON schema file
        write_disposition: WRITE_APPEND, WRITE_TRUNCATE, or WRITE_EMPTY
        autodetect: Whether to use auto-detection (overrides schema)
    """
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)

    # Load schema from JSON file
    with open(schema_path, 'r') as f:
        schema_json = json.load(f)
    
    # Convert JSON schema to BigQuery SchemaField objects
    schema = convert_schema_json_to_bq_schemafield(schema_json)

    # Configure load job
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=write_disposition,
        autodetect=autodetect,
        field_delimiter=',',
        quote_character='"',
        allow_quoted_newlines=True,
        encoding='UTF-8'
    )

    # Create table reference
    table_ref = client.dataset(dataset_id).table(table_id)

    # Run load job
    with open(csv_path, 'rb') as csv_file:
        job = client.load_table_from_file(
            csv_file,
            table_ref,
            job_config=job_config
        )

        try:
            job.result()  # Wait for job completion
            print(f"Loaded {job.output_rows} rows to {dataset_id}.{table_id}")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            raise

    # Verify the loaded table
    table = client.get_table(table_ref)
    print(f"Table schema:\n{table.schema}")
    print(f"Table description: {table.description}")
    return table