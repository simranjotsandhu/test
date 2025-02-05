def generate_sql(query):
    """Generate SQL from NL using fine-tuned Meta LLaMA 3.2 (1B)."""
    input_text = f"Question: {query}\nSQL:"
    
    # Tokenize input
    input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
    
    # Generate SQL
    with torch.no_grad():
        output = model.generate(input_ids, max_length=256)
    
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Example test query
test_query = "List the top 3 customers with the highest revenue in 2023."
generated_sql = generate_sql(test_query)

print("✅ Generated SQL Query:\n", generated_sql)
