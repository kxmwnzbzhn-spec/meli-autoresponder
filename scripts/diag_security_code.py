"""Probar más endpoints relacionados a operators/shipments para el código diario."""
import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID=me["id"]

endpoints = [
    f"/users/{USER_ID}/operators",
    f"/users/me/operators",
    f"/operators",
    f"/operators/me",
    f"/operators/{USER_ID}",
    f"/sellers/{USER_ID}/operators",
    f"/users/{USER_ID}/operators/code",
    f"/marketplace/seller/{USER_ID}/access_code",
    f"/shipments/operators/me/code",
    f"/users/{USER_ID}/billing_info",
    f"/post-purchase/v1/users/{USER_ID}/security_code",
    f"/post-purchase/v2/users/{USER_ID}/security_code",
    f"/me/security/access_code",
    f"/users/{USER_ID}/access_codes",
    f"/access_codes/{USER_ID}",
    f"/access_codes/me",
    f"/sellers/{USER_ID}/security",
    f"/sellers/me/security",
    f"/sellers/me/access_codes",
    f"/sellers/{USER_ID}/access_codes",
    f"/transports/operators/me",
    f"/marketplace/v1/users/me/access_code",
    f"/operations/operators/me",
    f"/post-purchase/sellers/me/access_code",
    f"/post-purchase/me/access_code",
    f"/users/{USER_ID}/dispatch_code",
    f"/dispatch_code/me",
    f"/dispatch_codes/{USER_ID}",
    f"/users/{USER_ID}/handover_code",
    f"/users/{USER_ID}/handoff_code",
    f"/users/{USER_ID}/dropoff_code",
]

found = []
for ep in endpoints:
    try:
        rr = requests.get(f"https://api.mercadolibre.com{ep}", headers=H, timeout=8)
        body = rr.text[:400]
        marker = ""
        if rr.status_code in (200, 401, 403):
            marker = f" ← {rr.status_code}"
            found.append((ep, rr.status_code, body[:300]))
        print(f"  {ep:55} → {rr.status_code}{marker}")
    except Exception as e:
        pass

print(f"\n=== Endpoints con respuesta interesante ===")
for ep, code, body in found:
    print(f"  [{code}] {ep}")
    print(f"     {body[:300]}")
