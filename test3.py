from transformers import AutoModelForCausalLM, AutoTokenizer

# Load Meta LLaMA 3.2 (1B)
model_name = "meta-llama/Meta-Llama-3.2-1B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

print("✅ Loaded Meta LLaMA 3.2 (1B) Model!")
