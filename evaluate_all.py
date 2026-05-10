import os
import glob
import pandas as pd
import jsonlines
import argparse
import subprocess
import re

def extract_first_question(jsonl_file):
    """Extracts the first question from a jsonl result file to use for mapping."""
    try:
        with jsonlines.open(jsonl_file) as reader:
            for data in reader:
                content = data.get('trajectory', [])
                if not content:
                    continue
                input_seq = content[-1].get('input_seq', '')
                question_matches = re.findall(r'Objective: (.*?)\nObservation', input_seq)
                if question_matches:
                    return question_matches[0]
    except Exception as e:
        print(f"Error reading {jsonl_file}: {e}")
    return None

def find_dataset_for_jsonl(jsonl_file, parquet_files):
    """Maps the jsonl file to the correct parquet file by searching for the first question."""
    q = extract_first_question(jsonl_file)
    if not q:
        return None
        
    for pq_file in parquet_files:
        try:
            df = pd.read_parquet(pq_file)
            for _, row in df.iterrows():
                if "extra_info" in row and "question" in row["extra_info"]:
                    if row["extra_info"]["question"] == q:
                        return pq_file
        except Exception as e:
            continue
            
    return None

def parse_val_output(output_str):
    """Parses stdout from val_answer.py or val_answer_model_based.py to extract metrics."""
    res = {}
    for line in output_str.split('\n'):
        if "问题数目" in line:
            res['total_questions'] = int(re.findall(r'\d+', line)[0])
        elif "回答正确数目" in line:
            res['correct_answers'] = int(re.findall(r'\d+', line)[0])
        elif "未回答数目" in line:
            res['unanswered'] = int(re.findall(r'\d+', line)[0])
        elif "平均步数" in line:
            res['avg_steps'] = float(re.findall(r'[\d\.]+', line)[0])
    
    if 'correct_answers' in res and 'total_questions' in res and res['total_questions'] > 0:
        res['accuracy'] = res['correct_answers'] / res['total_questions']
    else:
        res['accuracy'] = 0.0
        
    return res

def main():
    parser = argparse.ArgumentParser(description="Evaluate all results using rule-based and optionally LLM-based checks.")
    parser.add_argument('--use-llm', action='store_true', help='Enable LLM model-based checking (costs API credits)')
    parser.add_argument('--output', type=str, default='evaluation_summary.csv', help='Output CSV file')
    parser.add_argument('--results-dir', type=str, default='.', help='Directory containing the jsonl files (default: current directory)')
    args = parser.parse_args()

    # Find all test/validation parquet files in benchmark
    parquet_files = []
    for root, dirs, files in os.walk("benchmark"):
        for file in files:
            if ("test" in file or "validation" in file) and file.endswith(".parquet"):
                parquet_files.append(os.path.join(root, file))

    search_pattern = os.path.join(args.results_dir, "*_webarena_results*.jsonl")
    jsonl_files = glob.glob(search_pattern)
    if not jsonl_files:
        print(f"No result files found in {args.results_dir} matching *_webarena_results*.jsonl.")
        return

    results = []
    
    for j_file in jsonl_files:
        print(f"\nEvaluating {j_file}...")
        pq_file = find_dataset_for_jsonl(j_file, parquet_files)
        if not pq_file:
            print(f"  -> Could not find matching dataset in benchmark/ for {j_file}. Skipping.")
            continue
            
        print(f"  -> Matched with dataset: {pq_file}")
        
        # Determine method from filename if possible
        method = "unknown"
        if "_sft" in j_file: method = "sft"
        elif "_rft" in j_file: method = "rft"
        else: method = "base/rag"
        
        # Run Rule-based eval
        print("  -> Running rule-based evaluation (val_answer.py)...")
        cmd = ["python", "val_answer.py", "--data_path", pq_file, "--gen_file", j_file]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        rule_metrics = parse_val_output(proc.stdout)
        
        row = {
            "result_file": os.path.basename(j_file),
            "method": method,
            "dataset": os.path.basename(os.path.dirname(pq_file)),
            "dataset_path": pq_file,
            "rule_total": rule_metrics.get('total_questions', 0),
            "rule_correct": rule_metrics.get('correct_answers', 0),
            "rule_accuracy": f"{rule_metrics.get('accuracy', 0.0):.2%}",
            "rule_unanswered": rule_metrics.get('unanswered', 0),
            "rule_avg_steps": rule_metrics.get('avg_steps', 0.0)
        }
        
        # Run LLM-based eval
        if args.use_llm:
            print("  -> Running LLM-based evaluation (val_answer_model_based.py)...")
            output_jsonl = j_file.replace(".jsonl", "_llm_eval.jsonl")
            cmd = ["python", "val_answer_model_based.py", "--data_path", pq_file, "--gen_file", j_file, "--output_file", output_jsonl]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            llm_metrics = parse_val_output(proc.stdout)
            
            row.update({
                "llm_total": llm_metrics.get('total_questions', 0),
                "llm_correct": llm_metrics.get('correct_answers', 0),
                "llm_accuracy": f"{llm_metrics.get('accuracy', 0.0):.2%}",
                "llm_unanswered": llm_metrics.get('unanswered', 0),
                "llm_avg_steps": llm_metrics.get('avg_steps', 0.0)
            })
            
        results.append(row)
        
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    
    # Also save to JSON for easier nested reading if preferred
    json_output = args.output.replace('.csv', '.json')
    df.to_json(json_output, orient='records', indent=4)
    
    print(f"\n==================================================")
    print(f"Saved evaluation summary to: {args.output} and {json_output}")
    print(df.to_string(index=False))
    print(f"==================================================")

if __name__ == '__main__':
    main()
