# SQL BI Agent

## Overview
SQL BI Agent is a powerful Streamlit application that allows users to ask natural language questions about their data in BigQuery and receive instant SQL queries with visualizations. It leverages LangGraph workflows, LLM-based query generation, and automatic validation to ensure accuracy.

For a detailed explanation, check out my Medium post: [Medium Article](https://medium.com/@claudiofilho22/creating-a-sql-bi-agent-using-langgraph-vertex-ai-agent-builder-9c497d38de53)

## Features
- **Natural Language to SQL**: Converts user questions into SQL queries.
- **Automated Query Validation**: Uses BigQuery dry-run validation.
- **Interactive Data Visualization**: Generates and validates Python visualization code.
- **Streamlit UI**: User-friendly interface for asking questions and viewing results.

## Installation
To set up and run the SQL BI Agent locally, follow these steps:

### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SqlBIAgent
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Google Cloud authentication (necessary Google Cloud SDK):
   ```bash
   gcloud auth application-default login
   ```
5. Run the Streamlit app:
   ```bash
   streamlit run streamlit.py
   ```

## Usage
1. Enter a question in natural language (e.g., "Show sales trends by month").
2. Click the **Run** button.
3. The application will:
   - Retrieve relevant table schemas.
   - Generate an SQL query using an LLM.
   - Validate and execute the query in BigQuery.
   - Generate a data visualization.
4. View the SQL query and visualization output in the Streamlit UI.

## Project Structure
```
├── upload_datasets_in_bq.py     # Script to upload Datasets in BQ
├── prompts.py                   # Prompt templates for LLM
├── settings.py                  # Configuration settings
├── workflow.py                  # LangGraph workflow definitions
├── streamlit.py                 # Streamlit UI implementation
├── bq_functions.py              # BigQuery helper functions
├── utils.py                     # Utility functions
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
```

## Author  
Cláudio César  

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-blue?logo=linkedin)](https://www.linkedin.com/in/claudio-c%C3%A9sar-506961164/)



