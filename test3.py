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



from peft import LoraConfig, get_peft_model
import torch

# Configure LoRA
config = LoraConfig(
    r=8,             # LoRA rank (lower for faster training)
    lora_alpha=32,   # Scaling factor
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA to LLaMA model
model = get_peft_model(model, config)
model.print_trainable_parameters()

print("✅ LoRA Applied to Meta LLaMA 3.2 (1B)!")
