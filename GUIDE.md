# BrowserAgent — Project Guide

> **Paper:** [BrowserAgent: Building Web Agents with Human-Inspired Web Browsing Actions](https://arxiv.org/abs/2510.10666)  
> Accepted at **TMLR 2025** with a JC-award to present at ICML/ICLR/NeurIPS conferences.

---

## 🧠 What Is This Project?

BrowserAgent trains small LLMs (e.g., Qwen 2.5-7B) to act as **autonomous web browsing agents** capable of answering questions by navigating Wikipedia-like websites. The agents are trained using two paradigms:

- **SFT** — Supervised Fine-Tuning on curated browser trajectories
- **RFT** — Reinforcement Fine-Tuning using reward signals from answer correctness

---

## 📁 File Structure

```
BrowserAgent/
│
├── 🔑 ROOT SCRIPTS (Entry Points)
│   ├── run_model.py              # Main evaluation runner — sends questions to the agent
│   ├── run_model_nomemory.py     # Like run_model.py but without conversation history
│   ├── data_generate.py          # Generates SFT training data via agent rollouts
│   ├── data_generate_rft.py      # Same but for RFT mode
│   ├── judge_sft.py              # Judges quality of SFT rollout data
│   ├── judge_rft.py              # Same for RFT
│   ├── swift_switch.py           # Converts data to ms-swift training format
│   ├── val_answer.py             # Rule-based evaluation of model answers
│   ├── val_answer_model_based.py # LLM-judge evaluation of model answers
│   ├── val_answer_model.py       # Variant of model-based evaluation
│   ├── val_answer_context.py     # Context-based evaluation variant
│   ├── deploy_vllm.sh            # Shell script to deploy model via vLLM on port 5001
│   └── match1000.py              # Utility for matching/sampling 1000 examples
│
├── 📝 PROMPT FILES
│   ├── system_prompt_with_history_info.txt  # System prompt with action + info history
│   ├── system_prompt_click_nourl.txt        # Variant: click actions, no URL navigation
│   └── sys_eval_prompt.txt                  # Evaluation system prompt
│
├── 📦 mini_webarena/             # Core browser environment & agent library
│   ├── agent.py                  # PromptAgent class — decides next browser action
│   ├── browser_env.py            # ScriptBrowserEnv — Playwright-based browser env (Gymnasium)
│   ├── browser_actions.py        # All supported browser actions (click, type, scroll, goto…)
│   ├── browser_processors.py     # Processes page → accessibility tree / HTML observation
│   ├── browser_constants.py      # Constants used across the browser env
│   ├── browser_helpFunc.py       # Browser helper utilities
│   ├── browser_login.py          # Handles login flows for web environments
│   ├── env.py                    # Main env wrapper
│   ├── env_base.py               # Base environment class
│   ├── env_client.py             # Client interface for remote env
│   ├── env_worker.py             # WikiQAEnv — the actual Wiki Q&A environment worker
│   ├── evaluator.py              # Answer evaluator
│   ├── model.py                  # LLM model wrapper
│   ├── model_sglang.py           # SGLang-based model inference
│   ├── prompt.py                 # Prompt constructors (CoT etc.)
│   ├── prompt.json               # JSON prompt templates
│   ├── rl_utils.py               # RL utilities (rewards, rollouts)
│   ├── create_dataset.py         # Dataset creation utilities
│   ├── object_store.py           # Persistent key-value store (SQLite DB for env states)
│   └── utils.py                  # Shared utilities
│
├── 🖥️ server_script/
│   └── server.py                 # FastAPI server with /start and /step endpoints
│                                 # Manages browser env sessions keyed by session ID
│
├── 📊 eval_script/               # Standalone evaluation pipeline
│   ├── run_eval.py               # Full evaluation runner
│   ├── prompt_process.py         # Heavy prompt construction and processing
│   ├── sglang_api.py             # SGLang API interface
│   ├── model_api.py              # Generic model API
│   ├── convert_model.py          # Model format conversion
│   └── eval_scripts.sh           # Shell wrapper for eval
│
├── 🔧 verl-tool/                 # Git submodule: RL training framework
│   ├── verl/                     # VERL RL library
│   ├── verl_tool/                # Tool-augmented RL extensions
│   └── examples/train/wikiRL/   # wikiRL_server.sh — the tool server for RL training
│
├── output/                       # Screenshots and results output directory
└── setup.py / requirements.txt   # Package install files
```

---

## 🚀 How to Start the Browser Agent

The system requires **3 services running in separate terminals**.

### Prerequisites

Before starting, make sure you have:
1. A downloaded model from HuggingFace:
   - [BrowserAgent-SFT](https://huggingface.co/TIGER-Lab/BrowserAgent-SFT)
   - [BrowserAgent-RFT](https://huggingface.co/TIGER-Lab/BrowserAgent-RFT)
2. Benchmark data in the `benchmark/` folder (see [BrowserAgent-SeedData](https://huggingface.co/datasets/TIGER-Lab/BrowserAgent-SeedData))
3. Wikipedia Docker container running on port `22015` (or use the live public URL)

---

### Terminal 1 — Deploy the LLM via vLLM (port 5001)

```bash
conda activate browseragent
cd BrowserAgent
bash deploy_vllm.sh /path/to/your/model
```

This launches the fine-tuned Qwen model as an **OpenAI-compatible API** at `http://localhost:5001`.  
`run_model.py` and other scripts connect to it as a client.

> **Config tip:** Edit `deploy_vllm.sh` to change `CUDA_VISIBLE_DEVICES`, `TENSOR_PARALLEL_SIZE`, or `GPU_MEMORY_UTILIZATION` as needed.

---

### Terminal 2 — Start the Tool / Environment Server (port 30810)

```bash
conda activate browseragent
cd BrowserAgent
bash verl-tool/examples/train/wikiRL/wikiRL_server.sh
```

This starts the **wikiRL tool server** that manages Playwright browser sessions.  
It receives agent actions and returns browser observations (accessibility tree / HTML).

---

### Terminal 3 — Run the Agent

**For model evaluation:**
```bash
conda activate browseragent
cd BrowserAgent
python run_model.py --data_path /path/to/benchmark/nq/test.parquet
```

**For SFT data generation:**
```bash
python data_generate.py /path/to/output_file.jsonl /path/to/sft_data.jsonl
```

**For RFT data generation:**
```bash
python data_generate_rft.py /path/to/output_file.jsonl /path/to/rft_data.jsonl
```

---

## 🔄 High-Level Data Flow

```
Question
  │
  ▼
run_model.py
  │  ① calls /get_observation (reset)
  ▼
Tool Server (port 30810) ──► WikiQAEnv ──► Playwright launches Chromium
  │  returns observation (accessibility tree)
  ▼
LLM (port 5001)
  │  generates next action: click / type / goto / stop
  ▼
Tool Server
  │  executes action in browser, returns new observation
  ▼
  └── repeat up to 30 steps ──────────────────────────────┐
                                                           │
Agent outputs <conclusion>  ◄──────────────────────────────┘
  │
  ▼
Trajectory saved to JSONL
  │
  ▼
val_answer.py  (rule-based)
  or
val_answer_model_based.py  (LLM judge)
```

---

## 🔑 Purpose of Major Files

| File | Purpose |
|------|---------|
| `deploy_vllm.sh` | Launches the fine-tuned LLM as a vLLM server on **port 5001** |
| `run_model.py` | **Main eval script** — reads questions from parquet, runs multi-turn agent loop (up to 30 steps), saves trajectories to JSONL |
| `run_model_nomemory.py` | Same as above but the agent has no memory of previous actions in its prompt |
| `data_generate.py` | Runs rollouts using the agent to collect **SFT training data** |
| `data_generate_rft.py` | Same but structured for **RFT data collection** |
| `judge_sft.py` | Scores/filters generated SFT trajectories by answer correctness |
| `judge_rft.py` | Same for RFT trajectories |
| `swift_switch.py` | Converts judged trajectories to [ms-swift](https://github.com/modelscope/ms-swift) chat format for fine-tuning |
| `val_answer.py` | Rule-based accuracy check (exact/partial string match) |
| `val_answer_model_based.py` | Uses an LLM as a judge to evaluate free-form answer quality |
| `mini_webarena/browser_env.py` | **Core Playwright browser env** — wraps Chromium, handles screenshots, accessibility trees, and action execution |
| `mini_webarena/agent.py` | `PromptAgent` — given a trajectory + intent, calls the LLM and parses the next browser action |
| `mini_webarena/env_worker.py` | `WikiQAEnv` — the Wikipedia Q&A task environment used by the server |
| `mini_webarena/object_store.py` | SQLite-backed store that persists browser env state between server requests |
| `mini_webarena/browser_actions.py` | Definitions of all browser actions the agent can emit (click, type, scroll, goto, stop, etc.) |
| `mini_webarena/browser_processors.py` | Converts raw page content → structured accessibility tree or HTML observation for the LLM |
| `mini_webarena/prompt.py` | `CoTPromptConstructor` — builds chain-of-thought prompts from trajectory history |
| `mini_webarena/model_sglang.py` | SGLang-based LLM inference client |
| `server_script/server.py` | FastAPI server exposing `/start` and `/step` — manages concurrent browser sessions via `object_store` |
| `system_prompt_with_history_info.txt` | The system prompt that instructs the agent on its task, action format, and how to track history/conclusions |
| `eval_script/run_eval.py` | Standalone batch evaluation runner (alternative to `run_model.py`) |

---

## 🗂️ Training Pipeline Summary

```
1. Deploy base model via vLLM
      ↓
2. Run data_generate.py → raw rollout trajectories (JSONL)
      ↓
3. Run judge_sft.py → filter by answer quality
      ↓
4. Run swift_switch.py → convert to ms-swift format
      ↓
5. Fine-tune with ms-swift (SFT)
      ↓
6. (Optional) Run data_generate_rft.py + judge_rft.py → RFT data
      ↓
7. Fine-tune with VERL (RFT via verl-tool/)
      ↓
8. Run run_model.py + val_answer.py → Evaluate final model
```

---

## 🔗 Resources

| Resource | Link |
|----------|------|
| 📄 Paper (arXiv) | https://arxiv.org/abs/2510.10666 |
| 🌐 Project Page | https://tiger-ai-lab.github.io/BrowserAgent/ |
| 🤗 SFT Model | https://huggingface.co/TIGER-Lab/BrowserAgent-SFT |
| 🤗 RFT Model | https://huggingface.co/TIGER-Lab/BrowserAgent-RFT |
| 📊 Dataset | https://huggingface.co/datasets/TIGER-Lab/BrowserAgent-Data |
| 📊 Seed Dataset | https://huggingface.co/datasets/TIGER-Lab/BrowserAgent-SeedData |
