import os, requests
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
}).json()
tok = r['access_token']
H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}
CID = "5505476644"
SELLER = 3348766821

# Probar legacy mediations
URLS = [
    ("POST", f"https://api.mercadolibre.com/v1/mediations/{CID}/messages", {"message":"prueba"}),
    ("POST", f"https://api.mercadolibre.com/mediations/{CID}/messages", {"message":"prueba"}),
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/notifications", {"text":"prueba"}),
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/notes", {"text":"prueba","visible":True}),
    ("GET",  f"https://api.mercadolibre.com/v1/mediations/{CID}", None),
    ("GET",  f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/related-entities", None),
    # Endpoint viejo de notas/respuestas
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/responses", {"text":"prueba"}),
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/seller-response", {"text":"prueba"}),
    # Acción específica
    ("POST", f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/players/respondent/actions/send_message_to_complainant", {"text":"prueba","message":"prueba"}),
]
for method, url, body in URLS:
    try:
        if method == "POST":
            r = requests.post(url, headers=H, json=body, timeout=10)
        else:
            r = requests.get(url, headers=H, timeout=10)
        print(f"  {method:5} {url[-90:]} → {r.status_code}: {r.text[:180]}")
    except Exception as e:
        print(f"  ERR {url}: {e}")
