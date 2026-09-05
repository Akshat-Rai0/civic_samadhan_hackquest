#!/usr/bin/env python3
"""Script to download Moondream2 model weights into the local models directory."""

import os
import sys

# Prevent pyvips from attempting to dlopen missing C library libvips.42.dylib
import sys
sys.modules['pyvips'] = None

def download():
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("Please install requirements first: pip install -r requirements.txt")
        sys.exit(1)

    # Use 2024-08-26 revision which uses standard Pillow with no libvips C dependency
    model_id = "vikhyatk/moondream2"
    revision = "2024-08-26"
    target_dir = os.path.join(os.path.dirname(__file__), "..", "models", "moondream")
    target_dir = os.path.abspath(target_dir)

    print(f"Downloading Moondream weights ({model_id}, revision {revision})...")
    os.makedirs(target_dir, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, trust_remote_code=True)

    tokenizer.save_pretrained(target_dir)
    model.save_pretrained(target_dir)

    print(f"Model saved to {target_dir}")

if __name__ == "__main__":
    download()
