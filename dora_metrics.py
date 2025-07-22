import requests
from datetime import datetime, timedelta
import os
import json

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_PAT")  # use GH_PAT if that's the correct secret
REPO = "jitendractx/project01"
BRANCH = "main"
OUTPUT_FILE = "dora_metrics.json"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Get workflow runs ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    runs = response.json().get("workflow_runs", [])
    return [r for r in runs if r["conclusion"] == "success"]

# --- Calculate Deployment Frequency ---
def calculate_frequency(deployments):
    last_7_days = datetime.utcnow() - timedelta(days=7)
    recent = [
        d for d in deployments
        if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days
    ]
    return len(recent)

# --- Calculate Lead Time ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        pr_resp = requests.get(pr_url, headers={**HEADERS, "Accept": "application/vnd.github.groot-preview+json"})
        if pr_resp.status_code != 200:
            continue
        prs = pr_resp.json()
        if prs:
            merged_at = prs[0].get("merged_at")
            deployed_at = d["created_at"]
            if merged_at:
                merged_time = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
                deployed_time = datetime.strptime(deployed_at, "%Y-%m-%dT%H:%M:%SZ")
                lead_times.append((deployed_time - merged_time).total_seconds() / 3600)  # in hours
    return round(sum(lead_times) / len(lead_times), 2) if lead_times else 0

# --- Load previous data ---
def load_previous():
    if not os.path.exists(OUTPUT_FILE):
        return []
    try:
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

# --- Main ---
deployments = get_deployments()
frequency = calculate_frequency(deployments)
lead_time = calculate_lead_time(deployments)

# Append to historical log
previous = load_previous()
entry = {
    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "deployment_frequency": frequency,
    "average_lead_time_hours": lead_time
}
previous.append(entry)

# Write updated file
with open(OUTPUT_FILE, "w") as f:
    json.dump(previous, f, indent=2)

print("✅ DORA Metrics Updated")
