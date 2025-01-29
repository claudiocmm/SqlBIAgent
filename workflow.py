from typing import Dict, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain.schema import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_community import (
    VertexAISearchRetriever,
)
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
import pandas as pd

class AgentState(TypedDict):
    question: str
    database_schemas: str
    query: str
    num_retries_debug_sql: int
    max_num_retries_debug_sql: int
    result_debug_sql: str
    error_msg_debug_sql: str
    df: pd.DataFrame
    visualization_request: str
    python_code_data_visualization: str
    num_retries_debug_python_code_data_visualization: int
    max_num_retries_debug_python_code_data_visualization: int
    result_debug_python_code_data_visualization: str
    error_msg_debug_python_code_data_visualization: str


llm = ChatGroq(model="llama3-70b-8192", temperature=0)

retriever = VertexAISearchRetriever(
    project_id=settings.project_id,
    location_id="global",
    data_store_id="tables-descriptions_1738087630151",
    max_documents=2,
    engine_data_type=1
)


def search_tables_and_schemas(state: AgentState) -> AgentState:
    # tables = ["analytics-449112.supply_chain.locations"]

    docs_retrieved = retriever.invoke(state["question"])
    # tables_retrieved = retriever.invoke("I want to see the best movies in netflix")
    tables_metadata = [json.loads(doc.page_content) for doc in docs_retrieved]

    schemas = []
    bq_client = bigquery.Client(project=settings.project_id)
    for table_metadata in tables_metadata:
        project_id = table_metadata["project_id"]
        dataset_id = table_metadata["dataset_id"]
        table_id = table_metadata["table_id"]
        schema = bq_functions.get_table_schema(bq_client, project_id, dataset_id, table_id)
        if schema:
            schemas.append(schema)
    
    state["database_schemas"] = "\n---------------\n".join(schemas)
    return state


def agent_sql_writer_node(state: AgentState) -> AgentState:

    prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_sql_writer))

    chain = prompt_template | llm

    response = chain.invoke({"question": state["question"], 
                             "database_schemas": state["database_schemas"]}).content
    state["query"] = utils.extract_code_block(content=response,language="sql")
    print(f"### Agent SQL Writer query:\n {state["query"]}")
    return state



def agent_sql_validator_node(state: AgentState) -> AgentState:
    bq_client = bigquery.Client(settings.project_id) 
    

    print("\n\n### Validating query:")
    
    try:
        query = state["query"]
        # Configure a dry run job
        job_config = bigquery.QueryJobConfig(dry_run=True)
        # Start the query as a job (will not execute due to dry_run=True)
        query_job = bq_client.query(query, job_config=job_config)
        state["result_debug_sql"] = "Pass"
        state["error_msg_debug_sql"] = ""
        print(f"result: {state["result_debug_sql"]}")

        return state
        
    except Exception as e:
        state["num_retries_debug_sql"] += 1

        # return False, f"Error validating query: {str(e)}"
        state["result_debug_sql"] = "Not Pass"
        state["error_msg_debug_sql"] = str(e)
        print(f"result: {state["result_debug_sql"]}")
        print(f'error message: {state["error_msg_debug_sql"]}')

        #trying to fix the query
        print("\n### Trying to fix the query:")
        prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_sql_validator_node))

        chain = prompt_template | llm


        response = chain.invoke({"query": state["query"], 
                                "error_msg_debug": state["error_msg_debug_sql"]}).content

        state["query"] = utils.extract_code_block(content=response,language="sql")
        print(f"\n### Query adjusted:\n {state["query"]}")

        return state


def execute_query_node(state: AgentState) -> AgentState:
    # Initialize the BigQuery client
    bq_client = bigquery.Client(settings.project_id)

    df = bq_client.query(state["query"]).to_dataframe()

    state["df"] = df

    return state


def agent_bi_expert_node(state: AgentState) -> AgentState:
    
    prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_bi_expert_node))

    chain = prompt_template | llm

    response = chain.invoke({"question": state["question"],
                             "query": state["query"],
                             "df_structure": state["df"].dtypes,
                             "df_sample": state["df"].head(5)
                             }).content

    state["visualization_request"] = response
    print(f"\n### Visualization Request:\n {state["visualization_request"]}")

    return state


def agent_python_code_data_visualization_generator_node(state: AgentState) -> AgentState:

    prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_python_code_data_visualization_generator_node))

    chain = prompt_template | llm

    response = chain.invoke({"visualization_request": state["visualization_request"],
                             "df_structure": state["df"].dtypes,
                             "df_sample": state["df"].head(5)
                             }).content
    state["python_code_data_visualization"] = utils.extract_code_block(content=response,language="python")


    return state


def agent_python_code_data_visualization_validator_node(state: AgentState) -> AgentState:    

    print("\n\n### Validating data visualization code:")
    
    try:
        df = state["df"]
        exec(state["python_code_data_visualization"])
        state["result_debug_python_code_data_visualization"] = "Pass"
        state["error_msg_debug_python_code_data_visualization"] = ""
        print(f"result: {state["result_debug_python_code_data_visualization"]}")

        return state
        
    except Exception as e:
        state["num_retries_debug_python_code_data_visualization"] += 1

        # return False, f"Error validating query: {str(e)}"
        state["result_debug_python_code_data_visualization"] = "Not Pass"
        state["error_msg_debug_python_code_data_visualization"] = str(e)
        print(f"result: {state["result_debug_python_code_data_visualization"]}")
        print(f'error message: {state["error_msg_debug_python_code_data_visualization"]}')

        #trying to fix the query
        print("\n### Trying to fix the plotly code:")
        prompt_template = ChatPromptTemplate(("system", prompts.system_prompt_agent_python_code_data_visualization_validator_node))

        chain = prompt_template | llm


        response = chain.invoke({"python_code_data_visualization": state["python_code_data_visualization"], 
                                "error_msg_debug": state["error_msg_debug_python_code_data_visualization"]}).content

        state["python_code_data_visualization"] = utils.extract_code_block(content=response,language="python")

        print(f"\n### Plotly code adjusted:\n {state["python_code_data_visualization"]}")

        return state


workflow = StateGraph(state_schema=AgentState)


workflow.add_node("search_tables_and_schemas",search_tables_and_schemas)
workflow.add_node("agent_sql_writer_node",agent_sql_writer_node)
# workflow.add_node("agent_sql_reviewer_node",agent_sql_reviewer_node)
workflow.add_node("agent_sql_validator_node",agent_sql_validator_node)
workflow.add_node("execute_query_node",execute_query_node)
workflow.add_node("agent_bi_expert_node",agent_bi_expert_node)
workflow.add_node("agent_python_code_data_visualization_generator_node",agent_python_code_data_visualization_generator_node)
workflow.add_node("agent_python_code_data_visualization_validator_node",agent_python_code_data_visualization_validator_node)


workflow.add_edge("search_tables_and_schemas","agent_sql_writer_node")
# workflow.add_edge("agent_sql_writer_node","agent_sql_reviewer_node")
workflow.add_edge("agent_sql_writer_node","agent_sql_validator_node")

workflow.add_conditional_edges(
    'agent_sql_validator_node',
    lambda state: 'execute_query_node' 
    if state['result_debug_sql']=="Pass" or state['num_retries_debug_sql'] >= state['max_num_retries_debug_sql'] 
    else 'agent_sql_validator_node',
    {'execute_query_node': 'execute_query_node', 'agent_sql_validator_node': 'agent_sql_validator_node'}
)
workflow.add_edge("execute_query_node","agent_bi_expert_node")
workflow.add_edge("agent_bi_expert_node","agent_python_code_data_visualization_generator_node")
workflow.add_edge("agent_python_code_data_visualization_generator_node","agent_python_code_data_visualization_validator_node")

workflow.add_conditional_edges(
    'agent_python_code_data_visualization_validator_node',
    lambda state: "end" 
    if state['result_debug_python_code_data_visualization']=="Pass" or state['num_retries_debug_python_code_data_visualization'] >= state['max_num_retries_debug_python_code_data_visualization'] 
    else 'agent_python_code_data_visualization_validator_node',
    {'end': END,'agent_python_code_data_visualization_validator_node': 'agent_python_code_data_visualization_validator_node'}
)


workflow.set_entry_point("search_tables_and_schemas")

app = workflow.compile()

### Run workflow

def run_workflow(question: str) -> dict:
    initial_state = AgentState(
        question = question,
        database_schemas = "",
        query = "",
        num_retries_debug_sql = 0,
        max_num_retries_debug_sql = 3,
        result_debug_sql = "",
        error_msg_debug_sql = "",
        df = pd.DataFrame(),
        visualization_request = "",
        python_code_data_visualization = "",
        num_retries_debug_python_code_data_visualization = 0,
        max_num_retries_debug_python_code_data_visualization = 3,
        result_debug_python_code_data_visualization = "",
        error_msg_debug_python_code_data_visualization = ""
    )
    result = app.invoke(initial_state)
    return result

# state = run_workflow(question = "What are the released years with more released movies and tv shows in netflix. Show me a top 10 by two categories (movie and tv show)")
# state = run_workflow(question = "How many movies were released in 2020 in netflix?") 
# state = run_workflow(question = "What are the 3 video game platforms more sold in the history?") 