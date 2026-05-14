# Results & Reproduction Comparison

This file documents the reproduced evaluation numbers compared against the original paper's reported figures, and includes results for our proposed improvement — **Lexical URL Injection ("Hover State" Protocol)**.

> **How to regenerate these numbers:**
> ```bash
> python evaluate_all.py --results-dir ./results --use-llm
> ```

---

## Main Results: SFT vs. RFT Baselines (Reproduced)

Numbers are evaluated on pre-generated trajectories stored in `./results/`. Two evaluation modes are reported:
- **Rule-based** — exact/partial string match via `val_answer.py`
- **LLM-judge** — semantic correctness via `val_answer_model_based.py` (Llama-3.3-70B)

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

## Table 2 — Proposed Improvement: Lexical URL Injection

### The Idea

Standard WebArena accessibility trees present hyperlinks as plain text (e.g., `[42] link 'Director'`). The agent has no information about where the link leads, causing **semantic ambiguity** — the agent wastes steps clicking wrong links or timing out. We call this the "hover state" problem.

**Our fix:** At observation-parse time, we extract the underlying `href` attribute from the DOM via a single-pass Chrome DevTools Protocol (CDP) call and inject the terminal URL slug directly into the accessibility tree node:

```
Before: [42] link 'Director'
After:  [42] link 'Director' (URL: Christopher_Nolan)
```

### Implementation

The change is localized to `mini_webarena/browser_processors.py`:
- `extract_clean_url()` — maps raw Kiwix/Wikipedia hrefs to clean article slugs
- `parse_accessibility_tree()` — annotates all `link` role nodes with their destination URL
- Single-pass CDP call for href extraction — avoids per-node performance bottlenecks

### Results: Baseline vs. Lexical URL Injection (Rule-based EM)

> Trajectories are in `./results_base_model/`. Regenerate with:
> ```bash
> python evaluate_all.py --results-dir ./results_base_model
> ```

| Dataset   | Method | Baseline (EM) | + URL Injection (EM) | Δ         | Baseline Unanswered | New Unanswered | Δ Unanswered |
|-----------|--------|:-------------:|:--------------------:|:---------:|:-------------------:|:--------------:|:------------:|
| NQ        | SFT    |    41.50%     |       39.00%         |  -2.5%    |         46          |       47       |    +1        |
| NQ        | RFT    |    40.50%     |       42.00%         | **+1.5%** ✅ |      51          |       49       |    -2 ✅     |
| PopQA     | SFT    |    40.00%     |       44.00%         | **+4.0%** ✅ |      62          |       57       |    -5 ✅     |
| PopQA     | RFT    |    38.50%     |       38.50%         |   0.0%    |         49          |       50       |    +1        |
| HotpotQA  | SFT    |    40.50%     |       42.50%         | **+2.0%** ✅ |      69          |       59       |   -10 ✅     |
| HotpotQA  | RFT    |    46.50%     |       46.00%         |  -0.5%    |         50          |       57       |    +7 ❌     |
| 2Wiki     | SFT    |    49.00%     |       45.50%         |  -3.5% ❌ |         47          |       50       |    +3        |
| 2Wiki     | RFT    |    50.00%     |       45.00%         |  -5.0% ❌ |         42          |       43       |    +1        |
| MuSiQue   | SFT    |    16.00%     |       17.50%         | **+1.5%** ✅ |      79          |       91       |   +12 ❌     |
| MuSiQue   | RFT    |    14.00%     |       14.50%         | **+0.5%** ✅ |      94          |       95       |    +1        |
| Bamboogle | SFT    |    32.00%     |       26.40%         |  -5.6% ❌ |         52          |       67       |   +15 ❌     |
| Bamboogle | RFT    |    36.00%     |       31.20%         |  -4.8% ❌ |         51          |       52       |    +1        |
| **Avg.**  |        |  **37.04%**   |     **36.01%**       | **-1.03%** |        —           |        —       |              |

### Analysis

The results are **mixed with a slight overall regression** (-1.03% average). 5 datasets improved, 5 degraded, 2 were unchanged.

**Where it helped:** PopQA-SFT (+4.0%), HotpotQA-SFT (+2.0%), NQ-RFT (+1.5%), MuSiQue-SFT/RFT (+0.5–1.5%). HotpotQA-SFT unanswered dropped by 10 — the agent timed out less, which is consistent with the disambiguation hypothesis.

**Where it hurt:** 2Wiki-RFT (-5.0%), 2Wiki-SFT (-3.5%), Bamboogle-SFT (-5.6%), Bamboogle-RFT (-4.8%). Bamboogle-SFT saw unanswered spike by +15 — the agent exhausted its step budget more often, the opposite of what was expected.

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
| `val_answer_model_based.py` | LLM-judge evaluation (Llama-3.3-70B semantic judge) |
| `evaluate_all.py` | **Top-level script** — runs both evaluators across all result files, outputs `evaluation_summary.csv` |

### Regenerate Table 1 (baseline reproduction)

```bash
python evaluate_all.py --results-dir ./results --use-llm --output evaluation_summary.csv
```

### Regenerate Table 2 (URL injection results)

```bash
python evaluate_all.py --results-dir ./results_base_model --output evaluation_summary_urlinjection.csv
```

