import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen2.5-1.5B"
print(f"Loading {model_id} from Hugging Face cache...")

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype="auto",
    device_map="auto"
)
print("✅ Model loaded successfully into memory!\n")

prompt = "Explain in one sentence what SigNoz and open-source observability are."
messages = [
    {"role": "system", "content": "You are a helpful and concise AI assistant."},
    {"role": "user", "content": prompt}
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

print(f"User Prompt: \"{prompt}\"")
print("Generating response...\n")

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=100,
    temperature=0.7,
    do_sample=True
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print("--- Qwen 2.5 Response ---")
print(response.strip())
print("-------------------------")
