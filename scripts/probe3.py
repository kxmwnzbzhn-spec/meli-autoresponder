import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}", "Content-Type":"application/json"}
CID = "5505510642"

ENDPOINTS = [
    # More patterns to probe
    ("POST", f"/post-purchase/v1/claims/{CID}/decisions", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/decisions", {"decision":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/decision", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/seller-decisions", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/changes", {"action":"allow_return"}),
    ("POST", f"/post-purchase/v1/claims/{CID}/return", {}),
    ("POST", f"/post-purchase/v1/claims/{CID}/returns", {}),
    ("POST", f"/post-purchase/v1/claims/{CID}/refunds", {}),
    # Actions con resource
    ("POST", f"/post-purchase/v1/claims/{CID}/actions/respondent/allow_return", {}),
    # En path API v2 de mediaciones
    ("POST", f"/v2/mediations/{CID}/allow_return", {}),
    # endpoint de returns directo
    ("POST", f"/v1/returns", {"order_id": "2000016146104640"}),
    # Quizás es post-purchase/v2
    ("POST", f"/post-purchase/v2/claims/{CID}/actions/allow_return", {}),
    ("POST", f"/post-purchase/v2/claims/{CID}/actions", {"action":"allow_return"}),
    # Probar GET de las options disponibles
    ("GET",  f"/post-purchase/v1/claims/{CID}/actions", None),
    ("GET",  f"/post-purchase/v1/claims/{CID}/options", None),
    ("GET",  f"/post-purchase/v1/claims/{CID}/actions/respondent", None),
]
for method, path, body in ENDPOINTS:
    url = f"https://api.mercadolibre.com{path}"
    try:
        if method == "POST":
            r = requests.post(url, headers=H, json=body, timeout=10)
        else:
            r = requests.get(url, headers=H, timeout=10)
        print(f"{method:5} {path[-72:]} → {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  ERR: {e}")
