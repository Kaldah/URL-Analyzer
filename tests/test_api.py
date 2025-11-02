import json
import os
from pathlib import Path
import requests

API_URL = os.getenv("URL_ANALYZER_API", "http://127.0.0.1:8000/analyze")

def run_tests():
    # Resolve data.json relative to this file, not the current working directory
    data_file = Path(__file__).parent / "data.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Test data file not found: {data_file}")
    with data_file.open("r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"🔍 Running {len(test_data)} tests against {API_URL}\n")

    for test in test_data:
        test_number = test["test_number"]
        url = test["url"]
        expected = test["expected_output"]

        print(f"🧪 Test #{test_number} → {url}")

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Content-Type": "application/json"
                },
                json={"url": url},
                timeout=20
            )

            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}\n")
                continue

            data = response.json()
            print(f"✅ Response: {data}")

            # Compare with expected output
            mal = data.get("malicious_votes", -1)
            harm = data.get("harmless_votes", -1)

            # Simple evaluation (no strict assert as counts may vary)
            mal_ok = abs(mal - expected["malicious_votes"]) <= 2
            harm_ok = abs(harm - expected["harmless_votes"]) <= 10

            if mal_ok and harm_ok:
                print(f"✅ OK — within expected range\n")
            else:
                print(f"⚠️  Unexpected result:")
                print(f"   Expected: {expected}")
                print(f"   Got:      malicious={mal}, harmless={harm}\n")

        except requests.exceptions.RequestException as e:
            print(f"🚨 Request failed: {e}\n")


if __name__ == "__main__":
    run_tests()
