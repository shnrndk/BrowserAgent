#!/bin/bash

# Configuration
SAMPLE_SIZE=200
LOG_FILE="evaluation_mapping_base_model.log"
BENCHMARK_DIR="./benchmark"
OUTPUT_DIR="./results_base_model"

# Export vLLM environment variables to point to your local server
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="EMPTY"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# 1. Gather the list of datasets to process
declare -a pending_datasets

for dataset_dir in "$BENCHMARK_DIR"/*/ ; do
    # Remove trailing slash
    dataset_dir=${dataset_dir%/}
    dataset_name=$(basename "$dataset_dir")
    
    # Add to our pending list
    pending_datasets+=("$dataset_dir")
done

# 2. Print the execution order before starting
echo "========================================================"
echo "Planned Execution Order (Zero-Shot Baseline):"
echo "========================================================"
for dir in "${pending_datasets[@]}"; do
    echo "- $(basename "$dir")"
done
echo "========================================================"
echo ""
sleep 3

# Initialize log file
echo "Evaluation Run Mapping (Zero-Shot Baseline Run)" > "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "Sample Size: $SAMPLE_SIZE" >> "$LOG_FILE"
echo "Output Directory: $OUTPUT_DIR" >> "$LOG_FILE"
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
    
    # Record the number of result files in the ROOT directory BEFORE running
    before_files=$(ls -1 *_webarena_results.jsonl 2>/dev/null | wc -l)
    
    # Run the model WITHOUT the unsupported flags
    python run_model_base.py --data_path "$target_file" --num_samples "$SAMPLE_SIZE"
    
    # Wait briefly to ensure file I/O is completely flushed
    sleep 2
    
    # Check if a new file was created in the root directory
    after_files=$(ls -1 *_webarena_results.jsonl 2>/dev/null | wc -l)
    
    if [ "$after_files" -gt "$before_files" ]; then
        # Grab the newest file
        newest_result=$(ls -t *_webarena_results.jsonl 2>/dev/null | head -n 1)
        base_filename=$(basename "$newest_result")
        new_filepath="$OUTPUT_DIR/${dataset_name}_base_${base_filename}"
        
        # Move it to the designated folder
        mv "$newest_result" "$new_filepath"
        
        echo ""
        echo "Successfully completed $dataset_name."
        echo "Result moved to: $new_filepath"
        # Log the mapping
        echo "$target_file -> $new_filepath" >> "$LOG_FILE"
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