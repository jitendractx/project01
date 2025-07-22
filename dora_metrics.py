import requests
from datetime import datetime, timedelta
import os
import json
import sys

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_PAT") or os.getenv("GH_TOKEN")
REPO = "jitendractx/project01"  # Change to your repo
BRANCH = "main"

if not GITHUB_TOKEN:
    print("❌ GitHub token not found. Check if GH_PAT is set in secrets.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Get workflow runs (limit: 100) ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    runs = response.json().get("workflow_runs", [])
    return [r for r in runs if r["conclusion"] == "success"]

# --- Calculate Deployment Frequency ---
def calculate_frequency(deployments):
    last_7_days = datetime.now() - timedelta(days=7)
    recent = [
        d for d in deployments
        if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days
    ]
    return len(recent)

# --- Calculate Lead Time (PR merge to deploy) ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        pr_resp = requests.get(pr_url, headers={
            **HEADERS,
            "Accept": "application/vnd.github.groot-preview+json"
        })
        if pr_resp.status_code != 200:
            continue
        prs = pr_resp.json()
        if not prs:
            continue
        pr = prs[0]
        merged_at = pr.get("merged_at")
        if not merged_at:
            continue
        merged_time = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
        deployed_time = datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        lead_times.append((deployed_time - merged_time).total_seconds() / 3600)
    return round(sum(lead_times) / len(lead_times), 2) if lead_times else 0

# --- Run main ---
deployments = get_deployments()
frequency = calculate_frequency(deployments)
lead_time = calculate_lead_time(deployments)

result = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "deployment_frequency": frequency,
    "average_lead_time_hours": lead_time
}

# Append to history file
metrics_file = "docs/dora_metrics.json"
if os.path.exists(metrics_file):
    try:
        with open(metrics_file, "r") as f:
            history = json.load(f)
        if not isinstance(history, list):
            history = []
    except Exception:
        history = []
else:
    history = []

history.append(result)

with open(metrics_file, "w") as f:
    json.dump(history, f, indent=2)

print("✅ DORA Metrics Updated:", result)
