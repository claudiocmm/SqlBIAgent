from dotenv import load_dotenv
import os

PROJECT_CLIENT = "analytics-449112"

# Carrega as variáveis de ambiente e configura a chave da API da OpenAI
load_dotenv("/home/claudiocm/Git/SQLAgentReportCreator/.env")
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')


load_dotenv("/home/claudiocm/Git/SQLAgentReportCreator/.env")
os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')
