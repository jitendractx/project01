import requests
from datetime import datetime, timedelta
import os
import json

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO = "your-org/your-repo"
BRANCH = "main"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Get workflow runs (limit: 100) ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    runs = response.json()["workflow_runs"]
    return [r for r in runs if r["conclusion"] == "success"]

# --- Calculate Deployment Frequency ---
def calculate_frequency(deployments):
    last_7_days = datetime.now() - timedelta(days=7)
    recent_deploys = [d for d in deployments if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days]
    return len(recent_deploys)

# --- Calculate Lead Time (PR Merge → Deploy) ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        pr_resp = requests.get(pr_url, headers={**HEADERS, "Accept": "application/vnd.github.groot-preview+json"})
        prs = pr_resp.json()
        if prs:
            merged_at = prs[0]["merged_at"]
            deployed_at = d["created_at"]
            if merged_at:
                merged_time = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
                deployed_time = datetime.strptime(deployed_at, "%Y-%m-%dT%H:%M:%SZ")
                lead_times.append((deployed_time - merged_time).total_seconds() / 3600)  # in hours
    return sum(lead_times) / len(lead_times) if lead_times else 0

# --- Main ---
deployments = get_deployments()
frequency = calculate_frequency(deployments)
lead_time = calculate_lead_time(deployments)

result = {
    "deployment_frequency": frequency,
    "average_lead_time_hours": round(lead_time, 2)
}

with open("dora_metrics.json", "w") as f:
    json.dump(result, f, indent=2)

print("DORA Metrics Saved:", result)
