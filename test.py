from llama_index.core import SQLDatabase
from llama_index.core.indices.struct_store import GPTSQLStructStoreIndex

# from llama_index import SQLDatabase, GPTSQLStructStoreIndex
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


____

from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_index import SQLDatabase, GPTSQLStructStoreIndex
import sqlite3

# Load LLaMA model from Hugging Face (example for LLaMA 2)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")

# Initialize LLaMA-based model for querying
class LlamaLLM:
    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def generate(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

# Create an instance of the custom LLaMA class
llm = LlamaLLM(tokenizer, model)

# Connect to SQLite database
conn = sqlite3.connect("database.db")
sql_database = SQLDatabase(conn)

# Create index with LLaMA (using custom model interface)
index = GPTSQLStructStoreIndex.from_documents([], sql_database=sql_database, llm=llm)

# Perform a natural language SQL query
query = "What is the average sales price in the dataset?"
response = index.query(query)

print("Query Result:", response)
