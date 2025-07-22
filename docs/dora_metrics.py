import requests
from datetime import datetime, timedelta
import os
import json

# --- Config ---
GITHUB_TOKEN = os.getenv("GH_PAT")  # Match the workflow secret
REPO = "jitendractx/project01"      # Your actual repo path
BRANCH = "main"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Get successful workflow runs (limit: 100) ---
def get_deployments():
    url = f"https://api.github.com/repos/{REPO}/actions/runs"
    params = {"branch": BRANCH, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()  # Raise error if unauthorized or failed
    runs = response.json()["workflow_runs"]
    return [r for r in runs if r["conclusion"] == "success"]

# --- Calculate Deployment Frequency (last 7 days) ---
def calculate_frequency(deployments):
    last_7_days = datetime.utcnow() - timedelta(days=7)
    recent = [d for d in deployments if datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ") > last_7_days]
    return len(recent)

# --- Calculate Average Lead Time (PR Merge → Deploy) ---
def calculate_lead_time(deployments):
    lead_times = []
    for d in deployments:
        sha = d["head_sha"]
        pr_url = f"https://api.github.com/repos/{REPO}/commits/{sha}/pulls"
        pr_resp = requests.get(pr_url, headers={
            **HEADERS,
            "Accept": "application/vnd.github.groot-preview+json"
        })
        pr_resp.raise_for_status()
        prs = pr_resp.json()
        if prs:
            merged_at = prs[0].get("merged_at")
            deployed_at = d["created_at"]
            if merged_at:
                merged_time = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
                deployed_time = datetime.strptime(deployed_at, "%Y-%m-%dT%H:%M:%SZ")
                lead_times.append((deployed_time - merged_time).total_seconds() / 3600)  # in hours
    return round(sum(lead_times) / len(lead_times), 2) if lead_times else 0

# --- Main ---
if not GITHUB_TOKEN:
    print("❌ GitHub token not found. Check if GH_PAT is set in secrets.")
    exit(1)

try:
    deployments = get_deployments()
    frequency = calculate_frequency(deployments)
    lead_time = calculate_lead_time(deployments)

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "deployment_frequency": frequency,
        "average_lead_time_hours": lead_time
    }

    # Save as JSON
    with open("dora_metrics.json", "w") as f:
        json.dump(result, f, indent=2)

    print("✅ DORA Metrics Saved:", result)

except Exception as e:
    print("❌ Failed to calculate DORA metrics:", str(e))
    exit(1)
