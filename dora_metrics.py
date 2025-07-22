import requests
from datetime import datetime, timedelta
import os
import json

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_PAT")  # Use GH_PAT if that's what you configured
REPO = "jitendractx/project01"
BRANCH = "main"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Get workflow runs ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    runs = response.json().get("workflow_runs", [])
    return [r for r in runs if r["conclusion"] == "success"]

# --- Deployment Frequency ---
def calculate_frequency(deployments):
    last_7_days = datetime.utcnow() - timedelta(days=7)
    recent = [d for d in deployments if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days]
    return len(recent)

# --- Lead Time ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        resp = requests.get(pr_url, headers={**HEADERS, "Accept": "application/vnd.github.groot-preview+json"})
        prs = resp.json()
        if prs:
            merged_at = prs[0].get("merged_at")
            deployed_at = d["created_at"]
            if merged_at:
                merged = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
                deployed = datetime.strptime(deployed_at, "%Y-%m-%dT%H:%M:%SZ")
                lead_times.append((deployed - merged).total_seconds() / 3600)
    return sum(lead_times) / len(lead_times) if lead_times else 0

# --- Run Metrics ---
deployments = get_deployments()
frequency = calculate_frequency(deployments)
lead_time = calculate_lead_time(deployments)

# --- Append metrics to historical file ---
timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
entry = {
    "timestamp": timestamp,
    "deployment_frequency": frequency,
    "average_lead_time_hours": round(lead_time, 2)
}

filename = "dora_metrics.json"

if os.path.exists(filename):
    with open(filename, "r") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):  # safeguard
                data = [data]
        except json.JSONDecodeError:
            data = []
else:
    data = []

data.append(entry)

with open(filename, "w") as f:
    json.dump(data, f, indent=2)

print("✅ DORA metrics appended:", entry)
