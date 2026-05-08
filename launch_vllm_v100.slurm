#!/bin/bash
#SBATCH --job-name=vllm_v100         # Name visible in squeue
#SBATCH --output=logs/%j.log         # Standard output ( %j = Job ID)
#SBATCH --error=logs/%j.err          # Error log
#SBATCH --partition=gpu2v100         # Use V100 partition
#SBATCH --nodes=1                    # 1 node
#SBATCH --ntasks=1                   
#SBATCH --gres=gpu:2                 # Request 2 V100 GPUs (crucial for memory)
#SBATCH --cpus-per-task=8            # CPU threads for data loading
#SBATCH --mem=0                      # System RAM
#SBATCH --time=16:00:00              # Max wall-time (HH:MM:SS)

# Initialize conda for batch scripts
eval "$(conda shell.bash hook)"

# Activate your environment
conda activate browseragent
pip install uvloop "huggingface-hub<1.0" "opentelemetry-api<1.27.0" "opentelemetry-sdk<1.27.0" "protobuf==5.29.4"

# Navigate to the project directory
cd /work/gvx508/BrowserAgent

echo "Starting vLLM server on compute node: $(hostname) with 2x V100 GPUs"

# Launch the vLLM server using the V100 specific script
bash deploy_vllm_v100.sh /work/gvx508/BrowserAgent/BrowserAgent-SFT
