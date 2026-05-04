import requests
resp = requests.post("http://localhost:8000/api/generate", json={"prompt": "test", "mode": "voice"})
print("/api/generate Status:", resp.status_code)

resp = requests.post("http://localhost:8000/api/auth/login", json={"username": "test", "password": "password"})
print("/api/auth/login Status:", resp.status_code)
