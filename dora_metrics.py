import requests
from datetime import datetime, timedelta
import os
import json

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO = "jitendractx/project01"
BRANCH = "main"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def safe_get(url, headers, params=None):
    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        print(f"❌ Error {response.status_code} fetching {url}: {response.text}")
        response.raise_for_status()
    return response

# --- Get successful workflow runs ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = safe_get(url, HEADERS, params)
    runs = response.json().get("workflow_runs", [])
    return [r for r in runs if r["conclusion"] == "success"]

# --- Deployment Frequency ---
def calculate_frequency(deployments):
    last_7_days = datetime.utcnow() - timedelta(days=7)
    recent_deploys = [
        d for d in deployments
        if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days
    ]
    return len(recent_deploys)

# --- Lead Time for Changes ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        pr_resp = safe_get(pr_url, headers={**HEADERS, "Accept": "application/vnd.github.groot-preview+json"})
        prs = pr_resp.json()
        if prs and prs[0]["merged_at"]:
            merged_time = datetime.strptime(prs[0]["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
            deployed_time = datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            lead_times.append((deployed_time - merged_time).total_seconds() / 3600)
    return sum(lead_times) / len(lead_times) if lead_times else 0

# --- Collect new metrics ---
deployments = get_deployments()
frequency = calculate_frequency(deployments)
lead_time = calculate_lead_time(deployments)

new_entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "deployment_frequency": frequency,
    "average_lead_time_hours": round(lead_time, 2)
}

# --- Load existing metrics and append ---
file_path = "docs/dora_metrics.json"
if os.path.exists(file_path):
    try:
        with open(file_path, "r") as f:
            existing_data = json.load(f)
            if not isinstance(existing_data, list):
                existing_data = []
    except json.JSONDecodeError:
        existing_data = []
else:
    existing_data = []

existing_data.append(new_entry)

# --- Save updated history ---
with open(file_path, "w") as f:
    json.dump(existing_data, f, indent=2)

print("✅ DORA Metrics appended:", new_entry)
