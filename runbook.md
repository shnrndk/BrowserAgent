# BrowserAgent: HPC Cluster Runbook

This guide details how to run the BrowserAgent system on a shared SLURM cluster. 

The architecture requires **three distinct services** running simultaneously:
1. Local Wikipedia Server (Background process on the login node or a dedicated data node).
2. The LLM Server (vLLM on a compute node).
3. The Browser Tool Server (Ray/Playwright on the **same** compute node).
4. The Evaluator Script (Sends tasks to the system from the **same** compute node).

---

# Phase 1: One-Time Setup (Data & Environment)
*You only need to do this once.*

### 1. Download Models & Benchmark Data
Ensure your Hugging Face models and benchmark data are structured correctly in the project root:
* **Model:** `./BrowserAgent-SFT/`
* **Data:** `./benchmark/` (Contains subfolders like `nq`, `hotpot`, etc., with `.parquet` files).

For that run the following commands:

    python download_hf.py

### 2. Download and Run the Local Wikipedia Server
Because Docker and Podman require root privileges or clash with network file systems (NFS), we use the standalone Kiwix binary.

1. Download the `wikipedia_en_all_maxi_2022-05.zim` file (89GB) to your directory.
2. Download and extract the Kiwix tools:
   ```bash
   wget [https://download.kiwix.org/release/kiwix-tools/kiwix-tools_linux-x86_64-3.8.1.tar.gz](https://download.kiwix.org/release/kiwix-tools/kiwix-tools_linux-x86_64-3.8.1.tar.gz)
   tar -xvzf kiwix-tools_linux-x86_64-3.8.1.tar.gz
Run the server (You can run this on a tmux or screen session on your login node so it stays alive):

    ./kiwix-serve --port 22015 ./wikipedia_en_all_maxi_2022-05.zim 

# Phase 2: The 3-Terminal Execution Loop
⚠️ CRITICAL RULE: The LLM Server, Tool Server, and Evaluator script MUST all run on the exact same compute node (e.g., gpu040) so they can communicate over localhost.

Ensure you have requested a compute node with a modern architecture (like an A100) so vLLM can utilize bfloat16 and Flash Attention. (Do not use V100s unless you edit deploy_vllm.sh to use --dtype half).

## Step 1: Launch the LLM Server via SLURM (The Brain)
We use a SLURM script to request an A100 node and run vLLM in the background so it doesn't get killed by the login node.

Submit the job:

    sbatch launch_vllm.slurm

Use the following command to check for the assigned compute node:

    squeue -u <YOUR_USERNAME>

Check the output file (e.g., cat vllm_12345.out) to see which node the job was assigned to (e.g., gpu040) and wait until you see Uvicorn running on http://0.0.0.0:5001.

## Terminal 1: The LLM Server (The Brain)
Open a terminal, SSH into your assigned compute node, and start vLLM on port 5001.

### 1. Connect to your assigned compute node
    ssh <YOUR_COMPUTE_NODE>  # e.g., ssh gpu040

### 2. Activate environment
    conda activate browseragent
    cd /work/$USER/BrowserAgent

### 3. Launch vLLM
    bash deploy_vllm.sh ./BrowserAgent-SFT
Wait until you see: Application startup complete. and Uvicorn running on http://0.0.0.0:5001

## Terminal 2: The Tool Server (The Hands & Eyes)
Open a second terminal, SSH into the same compute node, and start the Ray/Playwright environment on port 30810.

Bash
### 1. Connect to the SAME compute node
    ssh <YOUR_COMPUTE_NODE>  # e.g., ssh gpu040

### 2. Activate environment
    conda activate browseragent
    cd /work/$USER/BrowserAgent

### 3. Launch Tool Server
    bash verl-tool/examples/train/wikiRL/wikiRL_server.sh
Wait until you see: Application startup complete. and Uvicorn running on http://0.0.0.0:30810
(Note: You can safely ignore any opentelemetry dashboard errors here as long as Uvicorn starts).

## Terminal 3: The Evaluator (The Teacher)
Open a third terminal, SSH into the same compute node, and launch the benchmark script.

### 1. Connect to the SAME compute node
    ssh <YOUR_COMPUTE_NODE>  # e.g., ssh gpu040

### 2. Activate environment
    conda activate browseragent
    cd /work/$USER/BrowserAgent

### 3. Run the evaluation
#### Make sure to point to the exact chunked parquet file name (e.g., test-00000-of-00001.parquet)
    python run_model.py --data_path ./benchmark/nq/test-00000-of-00001.parquet

## Troubleshooting

File Not Found (Parquet): HF datasets append chunk names to downloads. Use find ./benchmark -name "*.parquet" to get the exact file path to pass to --data_path.

vLLM Crash (Bfloat16 Error): If you are forced to use an older GPU (like a Tesla V100, Compute Capability 7.0), open deploy_vllm.sh and append --dtype half to the Python command.

Tool Server Hangs/Crashes: Ensure the local Wikipedia instance is actively running on port 22015 and reachable by the compute node. Check it with curl -I http://localhost:22015.