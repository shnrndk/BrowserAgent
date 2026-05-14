# BrowserAgent — Reproduction & Enhancement

**NLP Course Final Project (PhD)**  
*Reproducing and Improving [BrowserAgent: Building Web Agents with Human-Inspired Web Browsing Actions](https://arxiv.org/abs/2510.10666) — TMLR 2025*

---

## 📌 Project Overview

This repository contains a full, end-to-end reproduction of the **BrowserAgent** paper. BrowserAgent trains small LLMs (Qwen 2.5-7B) as autonomous web browsing agents capable of answering open-domain questions by navigating a local Wikipedia instance. Two training paradigms are reproduced:

- **SFT** — Supervised Fine-Tuning on curated browser trajectories
- **RFT** — Reinforcement Fine-Tuning using answer-correctness reward signals

Evaluation is performed across six multi-hop QA benchmarks: **2WikiMultiHopQA, HotpotQA, MuSiQue, Bamboogle, NQ, and PopQA**.

📊 **See [RESULTS.md](./RESULTS.md) for reproduced numbers, comparison to paper figures, and improvement results.**

---

## 🚀 Proposed Improvement: Lexical URL Injection

> 💻 **Implementation:** [`url-injection` branch](https://github.com/TIGER-AI-Lab/BrowserAgent/tree/url-injection) — [commit `f74a7cb`](https://github.com/TIGER-AI-Lab/BrowserAgent/commit/f74a7cbce3a434cf459468a149cce9d516839a4a)

### The Problem

When a BrowserAgent reads a Wikipedia page, it sees hyperlinks as plain text labels like:

```
[42] link 'Director'
[57] link 'Award'
[91] link 'Film'
```

The agent has **no idea where any of these links lead**. To find the article on Christopher Nolan, it might click `[42] link 'Director'` — only to land on the generic "Film director" disambiguation page. Now it's wasted a step, needs to go back, and try again. This is the **"hover state" problem**: a human would hover the mouse and see the URL (`/wiki/Christopher_Nolan`) before clicking — the agent is denied this basic affordance.

On multi-hop questions like *"Who directed the film that won the Academy Award for Best Picture in 2018?"*, this blind clicking compounds at every hop, causing the agent to exhaust its step budget and produce no answer at all.

### The Hypothesis

By programmatically injecting each link's destination URL slug into the accessibility tree at observation time — mimicking the information a human gets from hovering — the agent can:

1. **Avoid blind clicks** — it can read `(URL: Christopher_Nolan)` and know which link to choose before clicking
2. **Reduce wasted steps** — no more landing on wrong pages and backtracking
3. **Answer more questions** — fewer timeouts from step budget exhaustion on multi-hop chains

### The Implementation

The change is entirely in `mini_webarena/browser_processors.py` (see [commit `f74a7cb`](https://github.com/TIGER-AI-Lab/BrowserAgent/commit/f74a7cbce3a434cf459468a149cce9d516839a4a)):

```
Before: [42] link 'Director'
        [57] link 'Award'
        [91] link 'Film'

After:  [42] link 'Director'  (URL: Christopher_Nolan)
        [57] link 'Award'     (URL: Academy_Award_for_Best_Picture)
        [91] link 'Film'      (URL: Oppenheimer_(film))
```

- **`extract_clean_url()`** — converts raw Kiwix/Wikipedia hrefs to clean terminal article slugs, stripping encoding artifacts and redirect paths
- **`parse_accessibility_tree()`** — annotates every `link` role node with its destination slug using a single-pass Chrome DevTools Protocol (CDP) call (no per-link performance overhead)


---

## 🛠️ Frictionless Setup & Reproducibility

> **Key design decision for frictionless evaluation:** The time-intensive trajectory generation (LLM inference + browser interaction) has already been run and saved as `.jsonl` artifacts in `./results/`. You **do not** need to run the full agent pipeline to reproduce the tables — just run the evaluation script over the saved trajectories.

### Step 1 — Clone & Install

```bash
git clone <your-repo-url>
cd BrowserAgent
conda create -n browseragent python=3.10 -y
conda activate browseragent
pip install -r requirements.txt
playwright install chromium

# Create a .env file to hold your OpenAI API Key (required for the LLM Judge)
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Step 2 — Download Benchmark Data

> ⚠️ **The `benchmark/` directory is NOT included in the git repo** (it is gitignored due to file size). You must download it separately before running any evaluation.

```bash
python download_hf.py
```

This downloads both the model weights and the benchmark parquet files from HuggingFace into `./benchmark/`:

```
benchmark/
├── 2wiki/validation-00000-of-00001.parquet
├── hotpot/validation-00000-of-00001.parquet
├── musique/validation-00000-of-00001.parquet
├── nq/test-00000-of-00001.parquet
├── popqa/test-00000-of-00001.parquet
└── bamboogle/test-00000-of-00001.parquet
```

### Step 3 — Reproduce All Tables (One Command)

```bash
# Regenerate Table 1 from pre-saved SFT/RFT trajectories
python evaluate_all.py --results-dir ./results --use-llm
```

This runs **both** the rule-based (`val_answer.py`) and LLM-judge (`val_answer_model_based.py`) evaluators over all 12 result files and outputs `evaluation_summary.csv`.

> **Note on LLM Judging:** The `--use-llm` flag requires your `OPENAI_API_KEY` to be populated in the `.env` file (from Step 1) to utilize the GPT-4o/GPT-4o-mini consensus judges alongside the local Llama-3.3-70B judge endpoint. To skip LLM evaluation and run the rule-based (EM) pipeline only, simply omit the flag:
> ```bash
> python evaluate_all.py --results-dir ./results
> ```

---

## 📊 Reproducing the Paper's Tables

To easily reproduce both tables at once, use the unified wrapper script:
```bash
bash reproduce_all_tables.sh --use-llm
```

Alternatively, to regenerate each table individually:

### Table 1 — Main SFT/RFT Results

```bash
python evaluate_all.py --results-dir ./results --use-llm --output evaluation_summary_baseline.csv
```

### Table 2 — Proposed Improvement (URL Injection vs. Baseline)

```bash
python evaluate_all.py --results-dir ./results_novel --use-llm --output evaluation_summary_novel.csv
```

> 📄 Full reproduced numbers with paper comparison: **[RESULTS.md](./RESULTS.md)**

---

## 🖥️ Running the Full Pipeline (Optional)

If you want to regenerate trajectories from scratch rather than using the pre-saved artifacts, the system requires **4 services running in parallel**.

### 📥 Step 1: Prerequisites & Weights Setup

Ensure you've downloaded the model weights and benchmark datasets from HuggingFace using the provided helper script:

```bash
conda activate browseragent
# Downloads both BrowserAgent-RFT weights and seed benchmark parquet datasets
python download_hf.py
```

Ensure you also have:
- A local `kiwix-serve` instance of Wikipedia (`wikipedia_en_all_maxi_2022-05.zim`) running on port `22015`.
- An Nginx proxy (config: `custom_nginx.conf`) active to replicate WebArena's internal structure.

### 🎮 Step 2: Terminal Service Orchestration

You must run each of the following services in a separate terminal.

#### Terminal 0 — Start the Kiwix Content Proxy

This runs the localized Wikipedia content proxy designed to dynamically fix Kiwix navigation schemas and adapt the search tree for compatibility with the WebArena agent parsing pipeline:

```bash
conda activate browseragent
python proxy.py
```

#### Terminal 1 — Deploy the LLM via vLLM

**For Fine-tuned Models (SFT/RFT on port 5001):**
```bash
conda activate browseragent
bash deploy_vllm.sh /path/to/BrowserAgent-SFT
```

**For Basic Qwen Instruct (Baseline on port 8000):**
```bash
conda activate browseragent
python -m vllm.entrypoints.openai.api_server \
    --model ./models/Qwen2.5-7B-Instruct \
    --served-model-name qwen2.5-7b-instruct \
    --tensor-parallel-size 1 \
    --max-model-len 131072 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --dtype bfloat16 \
    --enforce-eager \
    --api-key sk-proj-1234567890
```

#### Terminal 2 — Start the Tool / Browser Server (port 30810)

The main environment coordinator that interfaces the agent's actions with Playwright instances:

```bash
conda activate browseragent
bash verl-tool/examples/train/wikiRL/wikiRL_server.sh
```

#### Terminal 3 — Run the Agent Trajectory Evaluation

**Running Fine-tuned Models:**
- **Single Dataset Run:** Test navigation on one specific benchmark file (e.g., Natural Questions test set):
  ```bash
  conda activate browseragent
  python run_model.py --data_path benchmark/nq/test-00000-of-00001.parquet
  ```
- **Full Suite Run:** Automatically run across all 6 benchmarks in sequence:
  ```bash
  conda activate browseragent
  bash run_all_evals.sh
  ```

**Running Qwen Instruct Baseline:**
```bash
conda activate browseragent
bash run_all_evals_base_instruct.sh
```
*(Or individually run `python run_model_base.py --data_path <path>`)*

All trajectory outputs are saved as `*_webarena_results_*.jsonl` in the root directory. Once complete, run `reproduce_all_tables.sh` to evaluate the accuracy.

---

## 📁 Repository Structure

```
BrowserAgent/
│
├── 🔑 Entry Points
│   ├── run_model.py                 # Main agent evaluation runner
│   ├── run_model_nomemory.py        # Agent without conversation history
│   ├── evaluate_all.py              # 🏆 Top-level evaluation script (reproduces all tables)
│   ├── val_answer.py                # Rule-based evaluator (exact/partial match)
│   └── val_answer_model_based.py    # LLM-judge evaluator (Llama-3.3-70B)
│
├── 📦 mini_webarena/                # Core browser environment & agent
│   ├── agent.py                     # PromptAgent — LLM → next browser action
│   ├── browser_env.py               # ScriptBrowserEnv (Playwright/Gymnasium)
│   ├── browser_processors.py        # ⭐ Accessibility tree parser (URL injection here)
│   ├── env_worker.py                # WikiQAEnv — Wikipedia Q&A task wrapper
│   └── ...
│
├── 📊 results/                      # Pre-generated SFT/RFT trajectories (Table 1)
├── 📊 results_novel/                # URL-injection trajectories (Table 2)
├── 📋 benchmark/                    # Benchmark datasets (Parquet)
│
├── 🔧 Training Pipeline
│   ├── data_generate.py             # SFT rollout data generation
│   ├── data_generate_rft.py         # RFT rollout data generation
│   ├── judge_sft.py / judge_rft.py  # Trajectory quality filtering
│   ├── swift_switch.py              # Convert to ms-swift training format
│   └── verl-tool/                   # VERL RL training framework (submodule)
│
├── RESULTS.md                       # 📄 Reproduced numbers & paper comparison
├── GUIDE.md                         # Detailed project internals guide
├── requirements.txt                 # Pinned dependencies
└── README.md                        # This file
```

---

## 🔗 Resources

| Resource | Link |
|----------|------|
| 📄 Paper (arXiv) | [arxiv.org/abs/2510.10666](https://arxiv.org/abs/2510.10666) |
| 🌐 Project Page | [tiger-ai-lab.github.io/BrowserAgent](https://tiger-ai-lab.github.io/BrowserAgent/) |
| 🤗 SFT Model | [TIGER-Lab/BrowserAgent-SFT](https://huggingface.co/TIGER-Lab/BrowserAgent-SFT) |
| 🤗 RFT Model | [TIGER-Lab/BrowserAgent-RFT](https://huggingface.co/TIGER-Lab/BrowserAgent-RFT) |
| 📊 Benchmark Data | [TIGER-Lab/BrowserAgent-SeedData](https://huggingface.co/datasets/TIGER-Lab/BrowserAgent-SeedData) |

---

## ⚖️ LLM Multi-Judge Consensus Evaluation

For semantic-based semantic evaluation, the pipeline utilizes `val_answer_model_based.py`. To maximize judgment robusteness and reduce individual model biases, it implements a **majority-vote consensus mechanism** consisting of three distinct LLM judges:

- **GPT-4o-mini**
- **GPT-4o**
- **Llama-3.3-70b-instruct-awq**

An agent's final answer is scored as **correct (1)** if and only if at least two out of the three judges reach a "Yes" consensus regarding semantic equivalence with the ground truth.

---

## 🔑 Fixed Seeds & Reproducibility Notes

- **Temperature:** `0.0` for all trajectory generation (deterministic decoding)
- **Dependencies:** Pinned in `requirements.txt` (Playwright 1.32.1, lxml 5.1.0, etc.)
- **Environment:** Evaluated against a local `kiwix-serve` Wikipedia instance routed through a local Nginx proxy to replicate the WebArena DOM structure
- **LLM Judge Endpoint:** Mixed multi-model voting via OpenAI API & UTSA local Llama endpoint.

---
