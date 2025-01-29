from llama_index import GPTSQLStructStoreIndex
from llama_index.llms import OpenAI
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Connection
import pandas as pd

# Example for SQLite, but this can be any database engine with SQLAlchemy
DATABASE_URL = "sqlite:///database.db"  # Change this to your database URL
engine = create_engine(DATABASE_URL)

# Create a connection to the database
conn = engine.connect()

# Example: Load a CSV into SQL (replace with your actual CSV file path)
csv_file = "data.csv"
df = pd.read_csv(csv_file)

# Load DataFrame into SQL table
df.to_sql('data_table', conn, if_exists='replace', index=False)

# Create a custom wrapper for the SQLAlchemy connection
class SQLAlchemyDatabase:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.inspector = inspect(connection)

    def get_usable_table_names(self):
        # Use SQLAlchemy's inspector to get table names
        return self.inspector.get_table_names()

    def get_single_table_info(self, table_name: str):
        # Fetch column information for the specified table using SQLAlchemy's inspector
        return self.inspector.get_columns(table_name)

    def query(self, query: str):
        # Execute a query and return results using SQLAlchemy's method
        result = self.connection.execute(query)
        return result.fetchall()

# Wrap the SQLAlchemy connection using the custom wrapper
sql_database = SQLAlchemyDatabase(conn)

# Initialize OpenAI model (you can replace with LLaMA or other models)
llm = OpenAI(model="gpt-4")

# Create index with SQLAlchemy engine and LLM
index = GPTSQLStructStoreIndex.from_documents([], sql_database=sql_database, llm=llm)

# Perform a natural language SQL query
query = "What is the average sales price in the dataset?"
response = index.query(query)

print("Query Result:", response)

# Close the connection when done
conn.close()
