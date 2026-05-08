import uuid
import requests
import json

def call_tool_server():
    env_url = "http://localhost:30810/get_observation"
    extra_fields = [{"url": "http://127.0.0.1:22015/content/wikipedia_en_all_maxi_2022-05/A/User%3AThe_other_Kiwix_guy/Landing"}]
    data = {
        "trajectory_ids": [str(uuid.uuid4())],
        "actions": [""],
        "finish": [False],
        "extra_fields": extra_fields
    }
    
    try:
        resp = requests.post(env_url, json=data, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "content": getattr(resp, 'text', '') if 'resp' in locals() else ''}

result = call_tool_server()
print("Result:", json.dumps(result, indent=2))
