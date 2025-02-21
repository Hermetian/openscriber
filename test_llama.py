import os
import sys

# Ensure environment variables are set before importing llama_cpp
os.environ["LLAMA_DISABLE_METAL"] = "1"
os.environ["GGML_METAL_DISABLE"] = "1"
os.environ["LLAMA_DISABLE_MLOCK"] = "1"

try:
    from llama_cpp import Llama
except ImportError:
    print("llama-cpp-python not installed. Please reinstall with Metal disabled.")
    sys.exit(1)

# Replace with the actual path to your model file
MODEL_PATH = "models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"

print("Loading model from:", MODEL_PATH)
try:
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=512,
        n_gpu_layers=0,     # Force CPU-only mode
        use_mlock=False,
        verbose=True        # Enable verbose logging
    )
    print("Model loaded successfully!")
except Exception as e:
    print("Failed to load model:")
    print(e)
