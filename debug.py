import requests
import json

# ==========================================================
# *** 여기에 당신의 API 키를 직접 붙여넣으세요 ***
# ==========================================================
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyIsImtpZCI6IktYMk40TkRDSTJ5NTA5NWpjTWk5TllqY2lyZyJ9.eyJpc3MiOiJodHRwczovL2x1ZHkuZ2FtZS5vbnN0b3ZlLmNvbSIsImF1ZCI6Imh0dHBzOi8vbHVkeS5nYW1lLm9uc3RvdmUuY29tL3Jlc291cmNlcyIsImNsaWVudF9pZCI6IjEwMDAwMDAwMDA0MjIxNDAifQ.cFbYLDgW2ZxFXBhY71_v2eEkKwgf0I1-2NDZhzdgBiEl9hyTgLjRMCQaSFkZdNnKFK0xe4rGaQe_-nVzbmxyXEHJTVijwEuADOaD-jv5wgSylpZNYqrjH11vmUtPLSWmU7Rel2tXOv9LCs_nd6fCrkDQsyV7ekiM_SyG0gCcB98v-BGfcbPo2Ds-xD5C-_i0BLg7DYHbRw5n1s1Z5lAgv2mP6o0rpd6bSacJUyhwB7UJhbVL4qNcborgKBSJROLOJl9nKsEUTosvARxT0H3boojuZBoqPXy-Uohog2jWfYYXP8uPpwdHgM9ZnBkw-EeKZW3pkm6YHe5dcqRJnnHg6A"
# ==========================================================

API_OPTIONS_URL = "https://developer-lostark.game.onstove.com/markets/options"

headers = {
    "accept": "application/json",
    "authorization": f"bearer {API_KEY}",
}

print("Fetching raw data from /markets/options API...")

try:
    response = requests.get(API_OPTIONS_URL, headers=headers)
    response.raise_for_status()
    
    # 응답받은 JSON 데이터를 예쁘게 출력
    raw_data = response.json()
    print("\n--- RAW API RESPONSE ---")
    print(json.dumps(raw_data, indent=2, ensure_ascii=False))
    
except requests.exceptions.RequestException as e:
    print(f"\nAPI call failed: {e}")
except json.JSONDecodeError:
    print("\nFailed to decode JSON from response. Response text:")
    print(response.text)