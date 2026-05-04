import requests
resp = requests.post("http://localhost:8000/api/auth/login/", json={"username": "test", "password": "password"})
print("Status:", resp.status_code)
print("Headers:", resp.headers)
print("Text:", resp.text)
