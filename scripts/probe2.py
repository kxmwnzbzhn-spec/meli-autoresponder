import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}

# Probar con varios claims para encontrar uno con allow_return disponible
CIDS = ["5505476644","5505521577","5505510642","5505319701","5505864377"]
for CID in CIDS:
    c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}", headers=H).json()
    for p in c.get("players", []):
        if p.get("role") == "respondent":
            actions = p.get("available_actions", [])
            print(f"\n[{CID}] respondent.available_actions:")
            for a in actions:
                print(f"  {json.dumps(a, indent=2, ensure_ascii=False)}")
            break
    if any(a.get('action')=='allow_return' for a in (p.get('available_actions') or [])):
        print(f"\n>>> {CID} TIENE allow_return — usando para test\n")
        break
