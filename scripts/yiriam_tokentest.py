"""Prueba directa del token YC_NEW: imprime la respuesta cruda de /oauth/token."""
import os, requests, json
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ.get("MELI_REFRESH_TOKEN_YC_NEW")
print(f"RT presente: {bool(RT)}  len={len(RT) if RT else 0}  prefix={(RT or '')[:12]}")
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT})
print(f"HTTP {r.status_code}")
print(json.dumps(r.json(), indent=2)[:600])
