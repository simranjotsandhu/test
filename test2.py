import chromadb

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("financial_data")

# Store schema & values in ChromaDB
for column in columns:
    sample_values = df[column].dropna().astype(str).unique()[:5].tolist()
    collection.add(
        documents=[f"Column: {column}, Sample Values: {', '.join(sample_values)}"],
        ids=[column]
    )

print("✅ Stored schema & values in ChromaDB!")
