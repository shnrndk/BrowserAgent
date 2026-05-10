import json

file_path = 'results/2wiki_webarena_results_sft.jsonl'
with open(file_path, 'r') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('trajectory', [])
        if not content: continue
        
        last_step = content[-1]
        output_seq = last_step.get('output_seq', '')
        if 'stop' not in output_seq:
            print("FOUND UNANSWERED EPISODE")
            input_seq = last_step.get('input_seq', '')
            idx = input_seq.find('Observation:\n')
            if idx != -1:
                obs = input_seq[idx:idx+2000]
                print(obs)
            print("\nFINAL OUTPUT:", output_seq)
            break
