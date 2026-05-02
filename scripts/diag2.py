import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
CID = "5505476644"

# Probar endpoints específicos para send_message_to_complainant
ENDPOINTS = [
    ("POST", f"/post-purchase/v1/claims/{CID}/players/respondent/messages", {"message":"test"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/actions/send_message_to_complainant", {"text":"test"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/actions/send_message_to_complainant", {"message":"test"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/actions/send-message-to-complainant", {"text":"test"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/messages-pack", {"text":"test"}),
    ("GET", f"/post-purchase/v1/claims/{CID}/expected-resolutions", None),
    ("GET", f"/post-purchase/v1/claims/{CID}/messages?include_attachments=true", None),
]
for m, path, body in ENDPOINTS:
    url = f"https://api.mercadolibre.com{path}"
    if m == "POST":
        r = requests.post(url, headers=H, json=body, timeout=10)
    else:
        r = requests.get(url, headers=H, timeout=10)
    print(f"{m} ...{path[-70:]} → {r.status_code}: {r.text[:200]}")

# Inspect the resolution and related_entities
c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}", headers=H).json()
print(f"\nresolution: {json.dumps(c.get('resolution'), indent=2)}")
print(f"related_entities: {json.dumps(c.get('related_entities'), indent=2)[:300]}")
