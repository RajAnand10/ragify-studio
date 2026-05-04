import requests

url = "http://localhost:8000/api/suggest-song"
data = {"prompt": "I want an energetic punjabi song for a workout"}

resp = requests.post(url, json=data)
print("Status:", resp.status_code)
print("Response:", resp.json())
