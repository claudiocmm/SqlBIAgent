from dotenv import load_dotenv
import os

project_id = "analytics-449112"
dataset_id = "datalake"
vertex_agent_builder_data_store_location_id = "global"
vertex_agent_builder_data_store_id = "tables-descriptions_1738087630151"

# Carrega as variáveis de ambiente e configura a chave da API da OpenAI
load_dotenv("/home/claudiocm/Git/SqlBIAgent/.env")
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')
