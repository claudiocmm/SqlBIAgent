from typing import Dict, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain.schema import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
import os
import prompts
import settings
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest, Forbidden
import bq_functions
import utils
import json

class AgentState(TypedDict):
    question: str
    database_schemas: str
    query: str
    num_revisions: int
    max_revisions: int
    result_debug: str


llm = ChatGroq(model="llama3-8b-8192", temperature=0)


def search_tables_and_schemas(state: AgentState) -> AgentState:
    tables = ["analytics-449112.supply_chain.locations"]
    schemas = []
    bq_client = bigquery.Client(project=settings.PROJECT_CLIENT)
    for table in tables:
        project_id = table.split(".")[0]
        dataset_id = table.split(".")[1]
        table_id = table.split(".")[2]
        schema = bq_functions.get_table_schema(bq_client, project_id, dataset_id, table_id)
        if schema:
            schemas.append(schema)
    
    state["database_schemas"] = "\n---------------\n".join(schemas)
    return state


def agent_sql_writer_node(state: AgentState) -> AgentState:

    prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_sql_writer))

    chain = prompt_template | llm

    response = chain.invoke({"question": state["question"], "database_schemas": state["database_schemas"]}).content
    state["query"] = utils.extract_only_sql_query(response)
    print(f"### Agent SQL Writer query:\n {state["query"]}")
    return state

    

def agent_sql_reviewer_node(state: AgentState) -> AgentState:
    print(f"Running SQL agent reviewer, revision {state["num_revisions"]}")
    prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_sql_reviewer_node))

    chain = prompt_template | llm

    response = chain.invoke({"query": state["query"], "database_schemas": state["database_schemas"]}).content

    state["query"] = utils.extract_only_sql_query(response)
    print(f"### Query reviewed:\n {state["query"]}")
    state["num_revisions"] += 1

    return state



def agent_debugger_sql_node(state: AgentState) -> AgentState:
    """
    Validates a BigQuery query using dry run without executing it.
    
    Args:
        query (str): The SQL query to validate
        project_id (str): Google Cloud project ID (optional)
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    bq_client = bigquery.Client(settings.PROJECT_CLIENT) 
    print("### Debugging query:")
    
    try:
        query = state["query"]
        # Configure a dry run job
        job_config = bigquery.QueryJobConfig(dry_run=True)
        # Start the query as a job (will not execute due to dry_run=True)
        query_job = bq_client.query(query, job_config=job_config)
        state["result_debug"] = "Pass"
        print(f"result: {state["result_debug"]}")
        return state
        
    except BadRequest as e:
        # Handle syntax errors and semantic errors
        # return False, f"Invalid query: {str(e)}"
        state["result_debug"] = "Not Pass"
        print(f"result: {state["result_debug"]}")
        return state
        
    except Forbidden as e:
        # Handle permission errors
        # return False, f"Permission denied: {str(e)}"
        state["result_debug"] = "Not Pass"
        print(f"result: {state["result_debug"]}")
        return state
        
    except Exception as e:
        # Handle other unexpected errors
        # return False, f"Error validating query: {str(e)}"
        state["result_debug"] = "Not Pass"
        print(f"result: {state["result_debug"]}")
        return state


def execute_query_node(state: AgentState):
    # Initialize the BigQuery client
    bq_client = bigquery.Client(settings.PROJECT_CLIENT)

    df = bq_client.query(state["query"]).to_dataframe()

    print(df)


workflow = StateGraph(state_schema=AgentState)


workflow.add_node("search_tables_and_schemas",search_tables_and_schemas)
workflow.add_node("agent_sql_writer_node",agent_sql_writer_node)
workflow.add_node("agent_sql_reviewer_node",agent_sql_reviewer_node)
workflow.add_node("agent_debugger_sql_node",agent_debugger_sql_node)
workflow.add_node("execute_query_node",execute_query_node)


workflow.add_edge("search_tables_and_schemas","agent_sql_writer_node")
workflow.add_edge("agent_sql_writer_node","agent_sql_reviewer_node")
workflow.add_edge("agent_sql_reviewer_node","agent_debugger_sql_node")
workflow.add_conditional_edges(
    'agent_debugger_sql_node',
    lambda state: 'execute_query_node' 
    if state['result_debug']=="Pass" or state['revision'] >= state['max_revision'] 
    else 'agent_sql_reviewer_node',
    {'execute_query_node': 'execute_query_node', 'agent_sql_reviewer_node': 'agent_sql_reviewer_node'}
)
workflow.add_edge("execute_query_node",END)

workflow.set_entry_point("search_tables_and_schemas")

app = workflow.compile()

### Run workflow

def run_workflow(question: str) -> dict:
    initial_state = AgentState(
        question = question,
        database_schemas = "",
        query = "",
        num_revisions = 0,
        max_revisions = 2,
        result_debug = ""
    )
    result = app.invoke(initial_state)
    return result

run_workflow(question = "Which locations has more different zip codes? Show me an top 10")