#!/bin/bash
# ============================================================
# reproduce_all_tables.sh
# Single entry point to regenerate ALL evaluation tables.
#
# Outputs:
#   evaluation_summary_baseline.csv    — Table 1 (SFT/RFT baseline)
#   evaluation_summary_urlinjection.csv — Table 2 (URL injection improvement)
#
# Usage:
#   bash reproduce_all_tables.sh            # rule-based only (fast)
#   bash reproduce_all_tables.sh --use-llm  # rule + LLM judge (requires API keys)
# ============================================================

LLM_FLAG=""
if [[ "$1" == "--use-llm" ]]; then
    LLM_FLAG="--use-llm"
    echo "🤖 LLM-judge mode enabled (GPT-4o-mini, GPT-4o, Llama-3.3-70B)."
else
    echo "📏 Rule-based only mode. Pass --use-llm to also run LLM judge."
fi

echo ""
echo "============================================================"
echo "Table 1: SFT/RFT Baseline (./results/)"
echo "============================================================"
python evaluate_all.py \
    --results-dir ./results \
    --output evaluation_summary_baseline.csv \
    $LLM_FLAG

echo ""
echo "============================================================"
echo "Table 2: URL Injection Improvement (./results_base_model/)"
echo "============================================================"
python evaluate_all.py \
    --results-dir ./results_base_model \
    --output evaluation_summary_urlinjection.csv \
    $LLM_FLAG

echo ""
echo "============================================================"
echo "✅ All done!"
echo "  Table 1 → evaluation_summary_baseline.csv"
echo "  Table 2 → evaluation_summary_urlinjection.csv"
echo "============================================================"
