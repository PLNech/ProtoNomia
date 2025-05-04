import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "deepseek-ai/Janus-Pro-7B"

# Enable 4-bit quantization and automatic device map (offloading)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",  # or "fp4"
    bnb_4bit_compute_dtype=torch.bfloat16
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model with quantization and offloading
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",  # Automatically offload layers to CPU if GPU VRAM is low
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

# Example inference from ./output/day_1_narrative.txt
prompt = open("./output/day_1_narrative.txt", "r").read()
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
