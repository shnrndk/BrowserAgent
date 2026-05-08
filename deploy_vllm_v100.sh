#!/bin/bash

# VLLM model deployment script tailored for V100 GPUs
# Usage: bash deploy_vllm_v100.sh /path/to/your/model

# Argument check
if [ -z "$1" ]; then
  echo "❌ Error: Please provide the model path as the first argument."
  exit 1
fi

MODEL_PATH="$1"
HOST="localhost"
PORT=5001

# VLLM parameter configuration for V100
TENSOR_PARALLEL_SIZE=2        # Use 2 GPUs since a single V100 doesn't have enough VRAM for a 125k context
MAX_MODEL_LEN=125000          # Keep massive context length
GPU_MEMORY_UTILIZATION=0.95   # Maximize memory use

# Set GPU environment variables
export CUDA_VISIBLE_DEVICES=0,1         # Use 2 GPUs
export NCCL_P2P_DISABLE=1               
export NCCL_IB_DISABLE=1                
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1  
export VLLM_ATTENTION_BACKEND=XFORMERS  # V100s lack native FlashAttention-2 support; Xformers is the most stable fallback
export VLLM_USE_TRITON_FLASH_ATTN=0     

echo "🚀 Starting the VLLM server for V100..."
echo "📁 Model path: $MODEL_PATH"
echo "🌐 Server address: http://$HOST:$PORT"
echo "🎮 GPUs in use: $CUDA_VISIBLE_DEVICES"
echo "🧠 Tensor parallel size: $TENSOR_PARALLEL_SIZE"

# Launch the VLLM API server
# CRITICAL: --dtype half is required because V100 (Volta architecture) does NOT support bfloat16 hardware acceleration
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    --served-model-name "qwen2.5-7b" \
    --trust-remote-code \
    --disable-log-requests \
    --api-key "sk-proj-1234567890" \
    --dtype half \
    --enforce-eager

echo "✅ V100 VLLM server has started successfully!"
