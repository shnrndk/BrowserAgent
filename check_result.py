import json
import re

file_path = 'results/2wiki_webarena_results_sft.jsonl'

print(f"Checking {file_path}...")
try:
    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            content = data.get('trajectory', [])
            if not content: continue
            
            output_seq = content[-1].get('output_seq', '')
            input_seq = content[-1].get('input_seq', '')
            
            if 'stop' not in output_seq:
                print("--- UNANSWERED TRAJECTORY FOUND ---")
                print(f"Trajectory Length: {len(content)}")
                
                # Check for conclusions in ANY step
                conclusions = []
                for step in content:
                    c = re.findall(r'<conclusion>(.*?)</conclusion>', step.get('output_seq', ''), re.DOTALL)
                    if c: conclusions.extend(c)
                
                print(f"Conclusions formed during trajectory: {len(conclusions)}")
                for i, c in enumerate(conclusions):
                    print(f"  [{i+1}] {c.strip()}")
                
                print("\nFINAL OBSERVATION (What the agent saw right before failing):")
                # the last input_seq contains the observation
                obs_matches = re.findall(r'Observation:\n(.*)', input_seq, re.DOTALL)
                if obs_matches:
                    print(obs_matches[0][:2000] + "\n... [TRUNCATED]")
                else:
                    print("No Observation block found in input_seq.")
                
                print("\nFINAL OUTPUT (What the agent did):")
                print(output_seq)
                print("-" * 50)
                break
except Exception as e:
    print('Error:', e)
