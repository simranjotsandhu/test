import pandas as pd
import sqlite3

# Load CSV as DataFrame
csv_file = "data.csv"
df = pd.read_csv(csv_file)

# Create SQLite Database
conn = sqlite3.connect("financial_data.db")
df.to_sql("financial_table", conn, if_exists="replace", index=False)

# Extract Schema
schema = {"table": "financial_table", "columns": list(df.columns)}
print("📊 Extracted Schema:", schema)

# Extract sample values for schema linking
sample_values = {col: df[col].dropna().unique()[:5].tolist() for col in df.columns}
print("📊 Sample Data Values:", sample_values)

