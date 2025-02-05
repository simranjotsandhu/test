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


## NEXT ##
from peft import LoraConfig, get_peft_model
from transformers import LlamaForCausalLM, LlamaTokenizer, Trainer, TrainingArguments

# Load LLaMA model & tokenizer
model_name = "llama-7b"
tokenizer = LlamaTokenizer.from_pretrained(model_name)
model = LlamaForCausalLM.from_pretrained(model_name)

# Configure LoRA (Lightweight Fine-Tuning)
config = LoraConfig(
    r=8, lora_alpha=32, lora_dropout=0.1,
    bias="none", task_type="CAUSAL_LM"
)
model = get_peft_model(model, config)

# Training Arguments
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    num_train_epochs=3,
    save_steps=10,
    output_dir="./llama_finetuned"
)

# Train Model
trainer = Trainer(model=model, args=training_args, train_dataset="train.json")
trainer.train()

# Save Fine-Tuned Model
model.save_pretrained("./llama_finetuned")
