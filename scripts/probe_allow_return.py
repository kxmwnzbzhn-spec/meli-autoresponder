import os, requests, json

# Usar Raymundo - 5505444213 (claim Go 4 Azul)
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
CID = "5505444213"

# Ver el estado actual y available_actions
c = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}", headers=H).json()
for p in c.get("players", []):
    if p.get("role") == "respondent":
        actions = p.get("available_actions", [])
        print(f"Available actions for respondent:")
        for a in actions:
            print(f"  • {a.get('action')}: due_date={a.get('due_date')}, mandatory={a.get('mandatory')}")
            if a.get("href"):
                print(f"    href: {a.get('href')}")

# Probar varios endpoints sin enviar realmente (usar dry-run si existe)
ENDPOINTS = [
    ("POST", f"/post-purchase/v1/claims/{CID}/actions/allow_return", {}),
    ("POST", f"/post-purchase/v1/claims/{CID}/actions", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/expected-resolutions", {"expected_resolution":"return_product"}),
    ("PUT",  f"/post-purchase/v1/claims/{CID}/expected-resolutions", {"expected_resolution":"return_product"}),
    ("PUT",  f"/post-purchase/v1/claims/{CID}/resolution", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/players/respondent/actions", {"action":"allow_return"}),
]
print("\n=== PROBE ENDPOINTS ===")
for method, path, body in ENDPOINTS:
    url = f"https://api.mercadolibre.com{path}"
    try:
        if method == "POST":
            r = requests.post(url, headers=H, json=body, timeout=10)
        else:
            r = requests.put(url, headers=H, json=body, timeout=10)
        print(f"{method:5} {path[-70:]} → {r.status_code}: {r.text[:250]}")
    except Exception as e:
        print(f"  ERR: {e}")
