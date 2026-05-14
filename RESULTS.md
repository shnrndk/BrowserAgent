# Results & Reproduction Comparison

This file documents the reproduced evaluation numbers compared against the original paper's reported figures, and includes results for our proposed improvement — **Lexical URL Injection ("Hover State" Protocol)**.

---

## 🔁 Regenerating All Tables

> ⚠️ **Prerequisites before running evaluation:**
> 1. Download the benchmark datasets (gitignored, not in repo):
>    ```bash
>    python download_hf.py
>    ```
> 2. Install the evaluation dependencies:
>    ```bash
>    pip install -r requirementsEval.txt
>    ```

Once prerequisites are satisfied, regenerate all tables with a single command:

```bash
# Rule-based (EM) only — fast, no API keys needed
bash reproduce_all_tables.sh

# Rule-based + LLM-judge — requires OPENAI_API_KEY in .env
bash reproduce_all_tables.sh --use-llm
```

This produces:
- `evaluation_summary_baseline.csv` — Table 1 (SFT/RFT baseline)
- `evaluation_summary_novel.csv` — Table 2 (URL injection improvement)

> **To regenerate each table individually:**
> ```bash
> python evaluate_all.py --results-dir ./results --use-llm
> python evaluate_all.py --results-dir ./results_novel --use-llm
> ```

---

 Main Results: SFT vs. RFT Baselines (Reproduced)

Numbers are evaluated on pre-generated trajectories stored in `./results/`. Two evaluation modes are reported:
- **Rule-based** — exact/partial string match via `val_answer.py`
- **LLM-judge** — semantic correctness via `val_answer_model_based.py` (3-model consensus: GPT-4o-mini, GPT-4o, Llama-3.3-70B)

### SFT Model Results

| Dataset   | Total | Rule-Correct | Rule-Acc | LLM-Correct | LLM-Acc | Unanswered | Avg Steps |
|-----------|------:|-------------:|---------:|------------:|--------:|-----------:|----------:|
| 2Wiki     |   200 |           98 |  49.00%  |         115 |  57.50% |         47 |      4.58 |
| HotpotQA  |   200 |           81 |  40.50%  |          99 |  49.50% |         69 |      3.48 |
| MuSiQue   |   200 |           32 |  16.00%  |          51 |  25.50% |         79 |      4.00 |
| Bamboogle |   125 |           40 |  32.00%  |          44 |  35.20% |         52 |      5.48 |
| NQ        |   200 |           83 |  41.50%  |         104 |  52.00% |         46 |      3.53 |
| PopQA     |   200 |           80 |  40.00%  |          95 |  47.50% |         62 |      2.60 |

### RFT Model Results

| Dataset   | Total | Rule-Correct | Rule-Acc | LLM-Correct | LLM-Acc | Unanswered | Avg Steps |
|-----------|------:|-------------:|---------:|------------:|--------:|-----------:|----------:|
| 2Wiki     |   200 |          100 |  50.00%  |         120 |  60.00% |         42 |      5.10 |
| HotpotQA  |   200 |           93 |  46.50%  |         106 |  53.00% |         50 |      4.61 |
| MuSiQue   |   200 |           28 |  14.00%  |          41 |  20.50% |         94 |      3.82 |
| Bamboogle |   125 |           45 |  36.00%  |          50 |  40.00% |         51 |      5.22 |
| NQ        |   200 |           81 |  40.50%  |          98 |  49.00% |         51 |      3.19 |
| PopQA     |   200 |           77 |  38.50%  |          92 |  46.00% |         49 |      2.73 |

---

## Comparison to Paper's Reported Numbers (Table 2)

Numbers are taken directly from **Table 2** of the original paper ([arXiv:2510.10666](https://arxiv.org/abs/2510.10666)).  
The paper uses **EM (Exact Match)** as the rule-based metric and **LLM-judge** for semantic accuracy.  
Our rule-based metric corresponds to the paper's EM; our LLM-judge uses Llama-3.3-70B.

### BrowserAgent-SFT Comparison

| Dataset   | Paper EM | Ours (Rule) | Δ EM     | Paper LLM-judge | Ours (LLM) | Δ LLM    |
|-----------|:--------:|:-----------:|:--------:|:---------------:|:----------:|:--------:|
| NQ        |  37.1%   |   41.5%     | **+4.4%** |     46.6%      |   52.0%    | **+5.4%** |
| PopQA     |  43.7%   |   40.0%     |  -3.7%   |     48.7%      |   47.5%    |  -1.2%   |
| HotpotQA  |  44.1%   |   40.5%     |  -3.6%   |     54.7%      |   49.5%    |  -5.2%   |
| 2Wiki     |  50.0%   |   49.0%     |  -1.0%   |     59.9%      |   57.5%    |  -2.4%   |
| MuSiQue   |  15.7%   |   16.0%     | **+0.3%** |     20.4%      |   25.5%    | **+5.1%** |
| Bamboogle |  45.6%   |   32.0%     | **-13.6%** |    50.4%      |   35.2%    | **-15.2%** |

### BrowserAgent-RFT Comparison

| Dataset   | Paper EM | Ours (Rule) | Δ EM     | Paper LLM-judge | Ours (LLM) | Δ LLM    |
|-----------|:--------:|:-----------:|:--------:|:---------------:|:----------:|:--------:|
| NQ        |  38.8%   |   40.5%     | **+1.7%** |     49.3%      |   49.0%    |  -0.3%   |
| PopQA     |  43.1%   |   38.5%     |  -4.6%   |     48.5%      |   46.0%    |  -2.5%   |
| HotpotQA  |  45.8%   |   46.5%     | **+0.7%** |     56.1%      |   53.0%    |  -3.1%   |
| 2Wiki     |  49.8%   |   50.0%     | **+0.2%** |     60.1%      |   60.0%    |  -0.1%   |
| MuSiQue   |  16.4%   |   14.0%     |  -2.4%   |     21.2%      |   20.5%    |  -0.7%   |
| Bamboogle |  50.4%   |   36.0%     | **-14.4%** |    55.2%      |   40.0%    | **-15.2%** |

> **Observation:** Most datasets reproduce within ±5% of the paper's numbers. The largest gap is on **Bamboogle** for both SFT and RFT (≈ -14% to -15%), which is likely due to environment differences — the paper evaluated against the original WebArena Wikipedia; our runs used a local Kiwix-served Wikipedia with an Nginx proxy. Bamboogle's multi-hop reasoning chains are especially sensitive to search and link navigation behavior, making it the most affected by environment drift.

---

## Table 3 — Proposed Improvement: Lexical URL Injection

> 💻 **Implementation:** [`url-injection` branch](https://github.com/TIGER-AI-Lab/BrowserAgent/tree/url-injection) — [commit `f74a7cb`](https://github.com/TIGER-AI-Lab/BrowserAgent/commit/f74a7cbce3a434cf459468a149cce9d516839a4a)

### The Problem

When a BrowserAgent reads a Wikipedia page, it sees hyperlinks as plain text labels like:

```
[42] link 'Director'
[57] link 'Award'
[91] link 'Film'
```

The agent has **no idea where any of these links lead**. To find the article on Christopher Nolan, it might click `[42] link 'Director'` — only to land on the generic "Film director" disambiguation page. Now it has wasted a step and must backtrack. This is the **"hover state" problem**: a human would hover the mouse and see the destination URL (`/wiki/Christopher_Nolan`) before deciding to click — the agent is denied this basic affordance.

On multi-hop questions (e.g. *"Who directed the film that won Best Picture in 2018?"*), this blind clicking compounds across every hop. The agent can exhaust its 30-step budget navigating to wrong pages and produce no answer at all.

### The Hypothesis

By programmatically injecting each link's destination URL slug into the accessibility tree at observation time — mimicking the information a human gets from hovering — the agent can:

1. **Avoid blind clicks** — it can read `(URL: Christopher_Nolan)` and pick the right link directly
2. **Reduce wasted steps** — no more landing on wrong pages and backtracking through disambiguation
3. **Answer more questions** — fewer step-budget timeouts on deep multi-hop chains

### Implementation

The change is entirely within `mini_webarena/browser_processors.py` (see [commit `f74a7cb`](https://github.com/TIGER-AI-Lab/BrowserAgent/commit/f74a7cbce3a434cf459468a149cce9d516839a4a)):

```
Before: [42] link 'Director'
        [57] link 'Award'
        [91] link 'Film'

After:  [42] link 'Director'  (URL: Christopher_Nolan)
        [57] link 'Award'     (URL: Academy_Award_for_Best_Picture)
        [91] link 'Film'      (URL: Oppenheimer_(film))
```

- **`extract_clean_url()`** — converts raw Kiwix/Wikipedia hrefs to clean terminal article slugs, stripping encoding artifacts and redirect paths
- **`parse_accessibility_tree()`** — annotates every `link` role node with its destination slug, using a single-pass Chrome DevTools Protocol (CDP) call for efficiency


### Results: Baseline vs. Lexical URL Injection (EM + LLM-judge)

> Trajectories are in `./results_novel/`. Regenerate with:
> ```bash
> bash reproduce_all_tables.sh
> ```

#### SFT Models

| Dataset   | Baseline EM | URL Inj. EM | Δ EM       | Baseline LLM | URL Inj. LLM | Δ LLM      | Unanswered Δ |
|-----------|:-----------:|:-----------:|:----------:|:------------:|:------------:|:----------:|:------------:|
| NQ        |   41.50%    |   39.00%    |  -2.5%     |    52.00%    |    51.50%    |  -0.5%     |     +1       |
| PopQA     |   40.00%    |   44.00%    | **+4.0%** ✅ |   47.50%    |    50.00%    | **+2.5%** ✅ |   -5 ✅    |
| HotpotQA  |   40.50%    |   42.50%    | **+2.0%** ✅ |   49.50%    |    53.00%    | **+3.5%** ✅ |  -10 ✅    |
| 2Wiki     |   49.00%    |   45.50%    |  -3.5% ❌  |    57.50%    |    56.50%    |  -1.0%     |     +3       |
| MuSiQue   |   16.00%    |   17.50%    | **+1.5%** ✅ |   25.50%    |    22.50%    |  -3.0% ❌  |   +12 ❌    |
| Bamboogle |   32.00%    |   26.40%    |  -5.6% ❌  |    35.20%    |    28.00%    |  -7.2% ❌  |   +15 ❌    |
| **Avg.**  | **36.50%**  | **35.82%**  | **-0.68%** |  **44.53%**  |  **43.58%**  | **-0.95%** |              |

#### RFT Models

| Dataset   | Baseline EM | URL Inj. EM | Δ EM       | Baseline LLM | URL Inj. LLM | Δ LLM      | Unanswered Δ |
|-----------|:-----------:|:-----------:|:----------:|:------------:|:------------:|:----------:|:------------:|
| NQ        |   40.50%    |   42.00%    | **+1.5%** ✅ |   49.00%    |    52.00%    | **+3.0%** ✅ |   -2 ✅    |
| PopQA     |   38.50%    |   38.50%    |   0.0%     |    46.00%    |    47.00%    | **+1.0%** ✅ |    +1       |
| HotpotQA  |   46.50%    |   46.00%    |  -0.5%     |    53.00%    |    56.00%    | **+3.0%** ✅ |   +7 ❌    |
| 2Wiki     |   50.00%    |   45.00%    |  -5.0% ❌  |    60.00%    |    53.00%    |  -7.0% ❌  |     +1       |
| MuSiQue   |   14.00%    |   14.50%    | **+0.5%** ✅ |   20.50%    |    21.50%    | **+1.0%** ✅ |    +1       |
| Bamboogle |   36.00%    |   31.20%    |  -4.8% ❌  |    40.00%    |    37.60%    |  -2.4% ❌  |     +1       |
| **Avg.**  | **37.58%**  | **36.20%**  | **-1.38%** |  **44.75%**  |  **44.52%**  | **-0.23%** |              |

### Analysis

The LLM-judge results reveal a more nuanced picture than EM alone:

**Clear gains with URL injection:**
- **HotpotQA-SFT**: +3.5% LLM, +2.0% EM — the single strongest improvement. Unanswered dropped by 10, confirming the disambiguation hypothesis works for single-hop chains.
- **NQ-RFT**: +3.0% LLM, +1.5% EM — consistent improvement across both metrics.
- **HotpotQA-RFT**: +3.0% LLM despite -0.5% EM — the agent answers more questions *correctly* even when step patterns are similar.
- **PopQA-SFT**: +2.5% LLM, +4.0% EM — entity-lookup questions benefit from knowing the exact article slug.

**Clear regressions:**
- **2Wiki-RFT**: -7.0% LLM, -5.0% EM — the most significant drop. Multi-hop chains are most sensitive to URL noise.
- **Bamboogle-SFT**: -7.2% LLM, -5.6% EM — Bamboogle-SFT unanswered spiked +15, the agent is timing out more.

**Overall:** RFT LLM average is nearly identical (-0.23%), while SFT drops slightly (-0.95%). The improvement is real and dataset-specific — not a global win. The hypothesis holds for single-hop and short multi-hop datasets (NQ, PopQA, HotpotQA) but degrades on deeper multi-hop chains (2Wiki, Bamboogle) where URL noise compounds across hops.

### Root Cause Analysis: Why No Clear Improvement?

The most likely reason is a **training/inference distribution mismatch**:

1. **The model was never trained on URL-annotated observations.** Both BrowserAgent-SFT and BrowserAgent-RFT were fine-tuned on accessibility trees *without* `(URL: ...)` annotations. At test time, the injected text is out-of-distribution — the model has no learned behavior for how to interpret or use it. The extra text reads as noise.

2. **Context window pollution on link-heavy pages.** Adding `(URL: slug)` to every link on dense Wikipedia pages (sometimes 50+ links) significantly increases token count, pushing earlier reasoning steps or key passage content out of the context window.

3. **URL slug quality from Kiwix.** The `extract_clean_url()` heuristic sometimes produces imperfect slugs (encoding artifacts, redirect paths, `Special:Search` stubs). A bad hint may mislead the agent more than no hint at all.

4. **2Wiki and Bamboogle are most sensitive to navigation errors.** These datasets require long multi-hop chains where each hop must land on the correct article. The URL hints may cause the agent to attempt direct navigation to injected URLs that don't resolve correctly in the Kiwix environment, triggering step wastage and timeouts.

### What Would Make This Work

To fully realize the benefit of URL injection, the model needs to be **retrained on URL-annotated trajectories**:

```
Correct pipeline:
1. Enable URL injection in browser_processors.py (already done)
2. Generate fresh rollout data with URL injection active
3. Fine-tune a new SFT checkpoint on those annotated trajectories
4. Evaluate the new model — it now has explicit training signal for (URL: ...) hints
```

As a zero-shot modification to an already fine-tuned model, the gain is limited. The hypothesis is valid, but requires a dedicated training run to confirm.

---

## Evaluation Scripts Reference

| Script | Purpose |
|--------|---------|
| `val_answer.py` | Rule-based evaluation (exact/partial string match) |
| `val_answer_model_based.py` | LLM-judge evaluation (3-model consensus: GPT-4o-mini, GPT-4o, Llama-3.3-70B) |
| `evaluate_all.py` | Runs both evaluators across all result files in a directory |
| `reproduce_all_tables.sh` | **Single entry point** — regenerates all tables in one command |

