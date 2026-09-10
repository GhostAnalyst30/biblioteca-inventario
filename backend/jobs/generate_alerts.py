import os
import urllib.request

api = os.environ.get("API_URL", "").rstrip("/")
if api and not api.startswith("http"):
    api = f"https://{api}"
secret = os.environ["ALERT_CRON_SECRET"]
url = f"{api}/api/jobs/generate-alerts?secret={secret}"
with urllib.request.urlopen(url, timeout=60) as resp:
    print(resp.read().decode())
