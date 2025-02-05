from transformers import TrainingArguments, Trainer

# Training arguments
training_args = TrainingArguments(
    output_dir="./llama3_1b_finetuned",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=50,
    save_total_limit=2,
    evaluation_strategy="steps",
    optim="adamw_torch",
    fp16=True,  # Mixed precision for efficiency
    push_to_hub=False
)

# Trainer instance
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["train"],
    tokenizer=tokenizer
)

# Start training
trainer.train()

print("✅ LoRA Fine-Tuning Completed!")
