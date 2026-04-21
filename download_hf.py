from huggingface_hub import snapshot_download, hf_hub_download

# 1. Download the Model (Choose SFT or RFT)
print("Downloading model...")
snapshot_download(
    repo_id="TIGER-Lab/BrowserAgent-SFT", 
    local_dir="./BrowserAgent-SFT"
)

# 2. Download the Seed Data
print("Downloading benchmark data...")
snapshot_download(
    repo_id="TIGER-Lab/BrowserAgent-SeedData", 
    repo_type="dataset",
    local_dir="./benchmark"
)
print("Done!")