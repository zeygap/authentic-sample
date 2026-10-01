"""Wait for the blueprint's public OIDC discovery, not just process health."""
import json
import time
from urllib.request import urlopen
url = "http://localhost:9000/application/o/sample/.well-known/openid-configuration"
for attempt in range(120):
    try:
        with urlopen(url, timeout=3) as response:
            data = json.load(response)
        assert data["issuer"] == "http://localhost:9000/application/o/sample/"
        print("authentik blueprint ready.")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Blueprint not ready. Run docker compose logs authentik-worker.")
