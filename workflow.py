from typing import Dict, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain.schema import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import os
import prompts
import settings
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest, Forbidden



class AgentState(TypedDict):
    question: str
    database_schema: str
    query: str
    num_revisions: int
    max_revisions: int
    result_debug: bool


llm = ChatGroq(model="llama3-8b-8192", temperature=0)


def agent_sql_writer_node(state: AgentState) -> AgentState:

    prompt_template = ChatPromptTemplate(prompts.system_prompt_agent_sql_writer)

    chain = prompt_template | llm

    response = chain.invoke({"question": state["question"], "database_schema": state["database_schema"]}).content
    state["query"] = response
    return state

    

def agent_sql_reviewer_node(state: AgentState) -> AgentState:
    prompt_template = ChatPromptTemplate(prompts.system_prompt_agent_sql_reviewer_node)

    chain = prompt_template | llm

    response = chain.invoke({"query": state["query"], "database_schema": state["database_schema"]}).content

    state["num_revisions"] += 1

    return state



def agent_debugger_sql_node(state: AgentState):
    """
    Validates a BigQuery query using dry run without executing it.
    
    Args:
        query (str): The SQL query to validate
        project_id (str): Google Cloud project ID (optional)
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    bq_client = bigquery.Client()
    
    try:
        query = state["query"]
        # Configure a dry run job
        job_config = bigquery.QueryJobConfig(dry_run=True)
        # Start the query as a job (will not execute due to dry_run=True)
        query_job = bq_client.query(query, job_config=job_config)
        
        return True, "Query is valid"
        
    except BadRequest as e:
        # Handle syntax errors and semantic errors
        return False, f"Invalid query: {str(e)}"
        
    except Forbidden as e:
        # Handle permission errors
        return False, f"Permission denied: {str(e)}"
        
    except Exception as e:
        # Handle other unexpected errors
        return False, f"Error validating query: {str(e)}"


def execute_query_node(state: AgentState):
    # Initialize the BigQuery client
    bq_client = bigquery.Client()

    bq_client.query(state["query"])


workflow = StateGraph(state_schema=AgentState)


workflow.add_node("agent_sql_writer_node",agent_sql_writer_node)
workflow.add_node("agent_sql_reviewer_node",agent_sql_reviewer_node)
workflow.add_node("agent_debugger_sql_node",agent_debugger_sql_node)
workflow.add_node("execute_query_node",execute_query_node)



workflow.add_edge("agent_sql_writer_node","agent_sql_reviewer_node")
workflow.add_edge("agent_sql_reviewer_node","agent_debugger_sql_node")
workflow.add_conditional_edges(
    'agent_debugger_sql_node',
    lambda state: 'execute_query_node' if state['result_debug']==True or state['revision'] >= state['max_revision'] else 'agent_sql_reviewer_node',
    {'execute_query_node': 'execute_query_node', 'agent_sql_reviewer_node': 'agent_sql_reviewer_node'}
)
workflow.add_edge("execute_query_node",END)

workflow.set_entry_point("agent_sql_writer_node")

workflow.compile()
