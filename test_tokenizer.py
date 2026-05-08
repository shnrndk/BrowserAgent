import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from transformers import AutoTokenizer

print("Loading tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained("./BrowserAgent-SFT")
    print("Tokenizer loaded successfully! Vocab size:", tokenizer.vocab_size)
except Exception as e:
    print("Error loading tokenizer:", e)
