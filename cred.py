import json
with open("firebase_credentials.json") as f:
    creds = json.load(f)
print(json.dumps(creds))
