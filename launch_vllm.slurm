#!/bin/bash
#SBATCH --job-name=vllm_server      # Name visible in squeue
#SBATCH --output=logs/%j.log         # Standard output ( %j = Job ID)
#SBATCH --error=logs/%j.err          # Error log
#SBATCH --partition=gpu1a100         # Use gpu1v100, titan, or gpu_rtx
#SBATCH --nodes=1                    # Always 1 for single-GPU LoRA
#SBATCH --ntasks=1                   
#SBATCH --gres=gpu:1                 # Request 1 Physical GPU
#SBATCH --cpus-per-task=4            # CPU threads for data loading
#SBATCH --mem=0                    # System RAM (adjust if OOM occurs)
#SBATCH --time=08:00:00              # Max wall-time (HH:MM:SS)

# Load the Anaconda/Miniconda module if your cluster requires it
# module load anaconda3

# Initialize conda for batch scripts
eval "$(conda shell.bash hook)"

# Activate your environment
conda activate browseragent
pip install uvloop "huggingface-hub<1.0" "opentelemetry-api<1.27.0" "opentelemetry-sdk<1.27.0" "protobuf==5.29.4"

sed -i 's/titan/titan/g' launch_vllm.slurm

# Navigate to the project directory
cd /work/gvx508/BrowserAgent

# Echo the hostname so you know exactly which compute node the server is running on
echo "Starting vLLM server on compute node: $(hostname)"

# Launch the vLLM server
bash deploy_vllm.sh /work/gvx508/BrowserAgent/BrowserAgent-SFT