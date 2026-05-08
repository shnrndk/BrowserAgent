import pandas as pd
import re
import jsonlines
import os
import asyncio
import time
from collections import deque
from openai import OpenAI
import argparse
import traceback
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="Run multi-turn response generation with customizable file paths.")
parser.add_argument('--data_path', type=str, 
                    default='', 
                    help='Path to the data file (e.g., /path/to/train.parquet)')
parser.add_argument('--gen_file', type=str, 
                    default='', 
                    help='Path to the gen_file')
parser.add_argument('--output_file', type=str, 
                    default='./test.jsonl', 
                    help='Output file path for writing the data (e.g., /path/to/output.jsonl)')
args = parser.parse_args()

with open("sys_eval_prompt.txt","r",encoding="utf-8") as f:
    eval_prompt = f.read()

# Load environment variables from a .env file
load_dotenv()

# Initialize the clients
client_openai = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1/"
)

# DeepSeek client removed as it cannot be resolved on the node

client_utsa = OpenAI(
    api_key="gpustack_50e00c9281422bc5_0c0696dfcb1696d7635e58a2e56d6282",
    base_url="http://10.246.100.230/v1"
)

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls  
        self.period = period        
        self.calls = deque()        
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                await asyncio.sleep(sleep_time)
            self.calls.append(time.time())

rate_limiter = RateLimiter(50, 60)

def get_response(prompt, model="gpt-4o-mini", temperature=0):
    # Route LLaMA to UTSA client, everything else to OpenAI
    if model == "llama-3.3-70b-instruct-awq":
        active_client = client_utsa
    else:
        active_client = client_openai

    try:
        response = active_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error fetching from {model}: {e}")
        return "Error"

async def same(question, gt, ans, sem, save_writer):
    prompt = eval_prompt.format(question, gt, ans)

    async def run(model):
        async with sem:  
            await rate_limiter.acquire()  
            return await asyncio.to_thread(get_response, prompt, model)

    # Added return_exceptions=True to prevent a full crash if one API drops
    answer_gpt_mini, answer_gpt_4o, answer_llama = await asyncio.gather(
        run("gpt-4o-mini"),
        run("gpt-4o"),      # Replaced deepseek-chat with gpt-4o
        run("llama-3.3-70b-instruct-awq"),
        return_exceptions=True 
    )

    print(answer_llama, answer_gpt_4o, answer_gpt_mini)

    save_writer.write({
        "question": question,
        "ground_truth": gt,
        "answer": ans,
        "gpt-4o-mini": answer_gpt_mini,
        "gpt-4o": answer_gpt_4o,             # Updated key to match the new model
        "llama-3.3-70b-instruct-awq": answer_llama
    })

    # Ensure we are checking string representations in case an exception was returned
    responses = [str(x) for x in [answer_llama, answer_gpt_4o, answer_gpt_mini]]
    yes_count = sum("yes" in x.lower() for x in responses)
    
    if yes_count >= 2:
        return 1
    return 0

async def main():
    data_df = pd.read_parquet(args.data_path)

    gt_answer = {
        row["extra_info"]["question"]: row["extra_info"]["selected_answer"]
        for _, row in data_df.iterrows()
    }

    with jsonlines.open(args.gen_file) as reader:   
        gen_data = list(reader)

    steps = 0
    suc = 0
    emp = 0

    sem = asyncio.Semaphore(10)

    with jsonlines.open(args.output_file, mode="w") as save_writer:

        async def process(data):
            nonlocal suc, steps, emp
            content = data['trajectory']
            input_seq = content[-1]['input_seq']
            output_seq = content[-1]['output_seq']

            question = re.findall(r'Objective: (.*?)\nObservation', input_seq)[0]

            if not re.findall(r"```(.*?)```", output_seq):
                answer = " "
            else:
                answer = re.findall(r"```(.*?)```", output_seq)[0]

            if 'stop' in answer:
                try:
                    ans = re.findall(r"\[(.*?)\]", answer)[0]
                except:
                    ans = ""
                ground_truth = gt_answer[question]
                try:
                    if await same(question, ground_truth, ans, sem, save_writer):
                        suc += 1
                        steps += data['trajectory_length']
                except Exception as e:
                    traceback.print_exc()
            else:
                emp += 1

        tasks = [process(data) for data in gen_data]
        await asyncio.gather(*tasks)

    print(f"问题数目：{len(gen_data)}")
    print(f"回答正确数目：{suc}")
    print(f"未回答数目：{emp}")
    print(f"平均步数：{steps/suc if suc > 0 else 0:.2f}")

if __name__ == "__main__":
    asyncio.run(main())