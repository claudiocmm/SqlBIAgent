import streamlit as st
import pandas as pd
import plotly.express as px
import workflow

# Page configuration
st.set_page_config(page_title="SQL BI Agent", layout="wide")

# Main application
st.title("📊 SQL BI Agent")

# Add welcome message and styling
st.markdown("""
<style>
    .stDataFrame {width: 100% !important;}
    .stTextInput input {font-size: 16px;}
    .welcome-msg {color: #2e86c1; font-size: 1.1rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="welcome-msg">Ask natural language questions about your data and get instant SQL queries with visualizations</p>', 
           unsafe_allow_html=True)

# Question input
question = st.text_input("Ask your data question:", 
                        placeholder="e.g., Show sales trends by month",
                        key="user_question")

if st.button("Run") and question:
    # Run the LangGraph workflow
    
    try:
        langraph_state = workflow.run_workflow(question)
        
        col1, col2 = st.columns([0.4,0.6])

        with col1:
            # Display generated SQL
            st.subheader("Generated SQL Query")
            st.code(langraph_state.get("query", "No SQL generated"), language="sql")

        with col2:
            # Display Charts
            st.subheader("Result")
            fig = langraph_state.get("python_code_store_variables_dict").get("fig", None)
            string_viz_result = langraph_state.get("python_code_store_variables_dict").get("string_viz_result", None)
            df_viz = langraph_state.get("python_code_store_variables_dict").get("df_viz", None)
            if fig is None:
                if df_viz is not None:
                    st.table(df_viz)
                else:
                    st.markdown(string_viz_result)
            else:
                st.plotly_chart(fig)
                
    except Exception as e:
        st.error(f"Error processing your request: {str(e)}")

elif not question:
    st.warning("Please enter a question")

