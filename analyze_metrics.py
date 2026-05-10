import json
import glob
import pandas as pd

def analyze_rag_metrics(rag_file="rag_metrics.jsonl"):
    print("="*50)
    print("1. CONTEXT EFFICIENCY & RAG OVERHEAD METRICS")
    print("="*50)
    
    try:
        data = []
        with open(rag_file, "r") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        
        if not data:
            print("rag_metrics.jsonl is empty.")
        else:
            df = pd.DataFrame(data)
            print(f"Total Steps Analyzed: {len(df)}")
            print(f"Average Pre-Filter Size:  {df['pre_filter_chars'].mean():.2f} characters")
            print(f"Average Post-Filter Size: {df['post_filter_chars'].mean():.2f} characters")
            print(f"Average Compression Ratio: {df['compression_ratio'].mean() * 100:.2f}% reduction")
            print(f"Average RAG Overhead Time: {df['rag_overhead_ms'].mean():.2f} ms per step")
            print(f"Average Functional Nodes Kept: {df['functional_nodes'].mean():.1f} per step")
            print(f"Average Semantic Nodes Kept:   {df['semantic_nodes'].mean():.1f} per step")
    except FileNotFoundError:
        print(f"'{rag_file}' not found.")
    except Exception as e:
        print(f"Error reading {rag_file}: {e}")

def analyze_llm_metrics():
    print("\n" + "="*50)
    print("2. LATENCY & AGENT BEHAVIOR METRICS")
    print("="*50)
    
    result_files = glob.glob("*webarena_results.jsonl")
    metrics_list = []
    
    for file in result_files:
        try:
            with open(file, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    traj_data = json.loads(line)
                    trajectory = traj_data.get("trajectory", [])
                    if trajectory and "metrics" in trajectory[-1]:
                        metrics_list.append(trajectory[-1]["metrics"])
        except Exception:
            pass
            
    if not metrics_list:
        print("No LLM metrics found in your *webarena_results.jsonl files.")
        print("Make sure an episode has fully completed to log the final metrics.")
    else:
        df = pd.DataFrame(metrics_list)
        print(f"Total Episodes Analyzed: {len(df)}")
        print(f"Average Episode Duration: {df['total_episode_duration'].mean():.2f} seconds")
        print(f"Average Inference Latency: {df['avg_infer_latency'].mean():.2f} seconds per step")
        print(f"Average Steps to Completion: {df['steps_to_completion'].mean():.2f} steps")
        print(f"Average Invalid Actions: {df['invalid_action_count'].mean():.2f} per episode")

if __name__ == "__main__":
    analyze_rag_metrics()
    analyze_llm_metrics()
