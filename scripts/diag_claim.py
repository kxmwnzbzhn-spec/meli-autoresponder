import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
CID = "5505476644"  # uno de Claribel
# 1) GET claim
c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}", headers=H).json()
print("CLAIM keys:", list(c.keys())[:20])
print(f"  status={c.get('status')} stage={c.get('stage')} reason={c.get('reason_id')} resource={c.get('resource')}/{c.get('resource_id')}")
for p in c.get("players",[]):
    print(f"  player {p.get('role')} actions={[a.get('action') for a in p.get('available_actions',[])]}")

# 2) Ver mensajes
m = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages", headers=H).json()
print(f"\nMESSAGES keys: {list(m.keys()) if isinstance(m,dict) else type(m)}")
if isinstance(m,dict):
    print(f"  count={len(m.get('messages',[]))}")
    for msg in m.get("messages",[])[:3]:
        print(f"  {msg.get('date_created','')[:19]} {msg.get('sender_role')}: {msg.get('message','')[:100]}")

# 3) Probar varios endpoints para enviar mensaje
ENDPOINTS = [
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages", {"message":"test"}),
    ("POST", f"https://api.mercadolibre.com/post-purchase/v2/claims/{CID}/messages", {"message":"test"}),
    ("POST", f"https://api.mercadolibre.com/v1/claims/{CID}/messages", {"message":"test"}),
]
print("\n=== PROBE ENDPOINTS ===")
for method, url, body in ENDPOINTS:
    if method == "POST":
        r = requests.post(url, headers=H, json=body, timeout=10)
    else:
        r = requests.get(url, headers=H, timeout=10)
    print(f"  {method} {url[-60:]} → {r.status_code}: {r.text[:150]}")
