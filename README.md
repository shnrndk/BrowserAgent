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

## 🚀 Proposed Improvement: Lexical URL Injection ("Hover State" Protocol)

### The Problem

In standard WebArena accessibility trees, the agent receives hyperlinks as bare text labels (e.g., `[42] link 'Director'`). Without destination information, the agent cannot distinguish between a useful entity link and a useless category page — it must *guess and click*, wasting trajectory steps and triggering timeouts.

### The Hypothesis

Human web navigation relies on the **"hover state"** — glancing at the destination URL before deciding to click. We hypothesize that *programmatically injecting the destination URL slug directly into the accessibility tree node* will:

1. Eliminate semantic ambiguity at link-selection time
2. Reduce exploratory misclicks and wasted steps
3. Decrease timeout-induced unanswered questions
4. Increase overall multi-hop accuracy

### The Implementation

The injection is localized to `mini_webarena/browser_processors.py`:

```
Before: [42] link 'Director'
After:  [42] link 'Director' (URL: Christopher_Nolan)
```

- `extract_clean_url()` — maps raw Kiwix/Wikipedia hrefs to clean terminal article slugs
- `parse_accessibility_tree()` — annotates all `link` role nodes with their destination URL
- Single-pass CDP call for href extraction — avoids per-node performance bottlenecks

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
```

### Step 2 — Download Benchmark Data

Datasets are stored in the `./benchmark/` directory in Parquet format.  
Source: [TIGER-Lab/BrowserAgent-SeedData](https://huggingface.co/datasets/TIGER-Lab/BrowserAgent-SeedData)

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

> **Note:** `--use-llm` requires a running Llama-3.3-70B judge endpoint. To skip LLM evaluation and use rule-based only, omit the flag:
> ```bash
> python evaluate_all.py --results-dir ./results
> ```

---

## 📊 Reproducing the Paper's Tables

The evaluation pipeline is structured so that **each table maps to a single command**:

### Table 1 — Main SFT/RFT Results

```bash
python evaluate_all.py --results-dir ./results --use-llm --output evaluation_summary.csv
```

### Table 2 — Proposed Improvement (URL Injection vs. Baseline)

```bash
python evaluate_all.py --results-dir ./resultsV2 --use-llm --output evaluation_summary_v2.csv
```

> 📄 Full reproduced numbers with paper comparison: **[RESULTS.md](./RESULTS.md)**

---

## 🖥️ Running the Full Pipeline (Optional)

If you want to regenerate trajectories from scratch rather than using the pre-saved artifacts, the system requires **3 services running in parallel**.

### Prerequisites

- A fine-tuned model checkpoint from HuggingFace:
  - [TIGER-Lab/BrowserAgent-SFT](https://huggingface.co/TIGER-Lab/BrowserAgent-SFT)
  - [TIGER-Lab/BrowserAgent-RFT](https://huggingface.co/TIGER-Lab/BrowserAgent-RFT)
- A local `kiwix-serve` instance of Wikipedia (`wikipedia_en_all_maxi_2022-05.zim`) running on port `22015`
- An Nginx proxy (config: `custom_nginx.conf`) to replicate WebArena's DOM structure

### Terminal 1 — Deploy the LLM via vLLM (port 5001)

```bash
conda activate browseragent
bash deploy_vllm.sh /path/to/BrowserAgent-SFT
```

### Terminal 2 — Start the Tool / Browser Server (port 30810)

```bash
conda activate browseragent
bash verl-tool/examples/train/wikiRL/wikiRL_server.sh
```

### Terminal 3 — Run the Agent

```bash
conda activate browseragent
# Run on a single benchmark (e.g., NQ test set)
python run_model.py --data_path benchmark/nq/test-00000-of-00001.parquet
```

Results are saved as `*_webarena_results_*.jsonl`. Pass the output directory to `evaluate_all.py` to score them.

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
├── 📊 resultsV2/                    # URL-injection trajectories (Table 2)
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

## 🔑 Fixed Seeds & Reproducibility Notes

- **Temperature:** `0.0` for all trajectory generation (deterministic decoding)
- **Dependencies:** Pinned in `requirements.txt` (Playwright 1.32.1, lxml 5.1.0, etc.)
- **Environment:** Evaluated against a local `kiwix-serve` Wikipedia instance routed through a local Nginx proxy to replicate the WebArena DOM structure
- **LLM Judge:** Llama-3.3-70B via UTSA cluster endpoint; minor stochasticity (< 1%) expected

---
