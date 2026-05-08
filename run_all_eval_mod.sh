#!/bin/bash

# Configuration
SAMPLE_SIZE=200
LOG_FILE="evaluation_mapping.log"
BENCHMARK_DIR="./benchmark"

# 1. Gather the list of datasets to process, excluding 2wiki
declare -a pending_datasets

for dataset_dir in "$BENCHMARK_DIR"/*/ ; do
    # Remove trailing slash
    dataset_dir=${dataset_dir%/}
    dataset_name=$(basename "$dataset_dir")
    
    # Skip the 2wiki directory
    if [ "$dataset_name" == "2wiki" ]; then
        continue
    fi
    
    # Add to our pending list
    pending_datasets+=("$dataset_dir")
done

# 2. Print the execution order before starting
echo "========================================================"
echo "Planned Execution Order:"
echo "========================================================"
for dir in "${pending_datasets[@]}"; do
    echo "- $(basename "$dir")"
done
echo "========================================================"
echo ""
sleep 3 # Pauses for 3 seconds so you can read the list before it starts

# Initialize log file
echo "Evaluation Run Mapping (Resumed Run)" > "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "Sample Size: $SAMPLE_SIZE" >> "$LOG_FILE"
echo "--------------------------------------------------------" >> "$LOG_FILE"

# 3. Execute the processing loop using our filtered list
for dataset_dir in "${pending_datasets[@]}" ; do
    dataset_name=$(basename "$dataset_dir")
    
    # Determine the target file (prefer test, then validation)
    target_file=""
    if ls "$dataset_dir"/*test*.parquet 1> /dev/null 2>&1; then
        target_file=$(ls "$dataset_dir"/*test*.parquet | head -n 1)
    elif ls "$dataset_dir"/*validation*.parquet 1> /dev/null 2>&1; then
        target_file=$(ls "$dataset_dir"/*validation*.parquet | head -n 1)
    else
        echo "Skipping $dataset_name: No test or validation file found."
        continue
    fi
    
    echo ""
    echo "========================================================"
    echo "Processing dataset: $dataset_name"
    echo "Target file: $target_file"
    echo "========================================================"
    
    # Record the number of result files before running
    before_files=$(ls -1 *_webarena_results.jsonl 2>/dev/null | wc -l)
    
    # Run the model
    python run_model.py --data_path "$target_file" --num_samples "$SAMPLE_SIZE"
    
    # Wait briefly to ensure file I/O is completely flushed
    sleep 2
    
    # Find the newest generated result file
    newest_result=$(ls -t *_webarena_results.jsonl 2>/dev/null | head -n 1)
    after_files=$(ls -1 *_webarena_results.jsonl 2>/dev/null | wc -l)
    
    if [ "$after_files" -gt "$before_files" ]; then
        echo ""
        echo "Successfully completed $dataset_name."
        echo "Result saved to: $newest_result"
        # Log the mapping
        echo "$target_file -> $newest_result" >> "$LOG_FILE"
    else
        echo ""
        echo "Warning: No new result file detected for $dataset_name!"
        echo "$target_file -> FAILED_TO_GENERATE" >> "$LOG_FILE"
    fi
done

echo ""
echo "========================================================"
echo "All evaluations completed!"
echo "You can find the mapping between datasets and results in: $LOG_FILE"
echo "========================================================"