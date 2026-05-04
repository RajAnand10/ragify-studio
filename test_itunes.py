import requests
url = "https://itunes.apple.com/search?term=lion+roar+sound+effect&entity=song&limit=1"
resp = requests.get(url)
data = resp.json()
print("Count:", data.get("resultCount"))
if data.get("resultCount", 0) > 0:
    print("Preview URL:", data["results"][0].get("previewUrl"))
