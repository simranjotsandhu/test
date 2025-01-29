# test

import pandas as pd
import sqlite3

# Load CSV into Pandas DataFrame
csv_file = "data.csv"  # Replace with your actual file path
df = pd.read_csv(csv_file)

# Create SQLite database
conn = sqlite3.connect("database.db")

# Load DataFrame into SQL table
df.to_sql("data_table", conn, if_exists="replace", index=False)

print("✅ Data loaded into SQLite!")
