from llama_index import SQLDatabase, GPTSQLStructStoreIndex
from llama_index.llms import LlamaCPP
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load a local LLaMA model (adjust for your system)
model_path = "TheBloke/Llama-2-7B-Chat-GGML"  # Example Hugging Face model
llm = LlamaCPP(model_path=model_path, temperature=0.1)

# Connect to SQLite
sql_database = SQLDatabase(conn)

# Create an index using LLaMA as the backend
index = GPTSQLStructStoreIndex.from_documents([], sql_database=sql_database, llm=llm)

# Perform a natural language query
query = "What is the average sales price in the dataset?"
response = index.query(query)

print("Query Result:", response)
