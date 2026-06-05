import json
import time
from datetime import datetime, timedelta
import urllib.request
import sys

# Automation script to trigger 100 runs for 100 days
# Usage: python generate_runs.py [setup_id] [start_date]
# Example: python generate_runs.py 1 2025-01-01

def trigger_job(setup_id, start_date, end_date):
    url = "http://localhost:8000/api/jobs/trigger-full"
    data = {
        "setup_id": int(setup_id),
        "start_date": start_date,
        "end_date": end_date,
        "alpha": 0.001,
        "grid_fee": 0.01
    }
    
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(data)
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    
    try:
        with urllib.request.urlopen(req, jsondataasbytes) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    setup_id = sys.argv[1] if len(sys.argv) > 1 else 2
    start_str = sys.argv[2] if len(sys.argv) > 2 else "2024-01-01"
    
    current_date = datetime.strptime(start_str, "%Y-%m-%d")
    
    print(f"🚀 Starting 1, 670 runs for Setup ID {setup_id} starting from {start_str}...")
    
    for i in range(1, 670):
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"[{i}/100] Triggering job for {date_str}...")
        
        res = trigger_job(setup_id, date_str, date_str)
        print(f"   Response: {res}")
        
        current_date += timedelta(days=1)
        time.sleep(0.5)

    print("✅ Finished triggering 100 jobs.")
