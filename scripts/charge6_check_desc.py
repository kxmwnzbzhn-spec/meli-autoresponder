"""Verificar descripciones de los 3 Charge 6 nuevos."""
import os, requests
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

ITEMS = ["MLM2894654315","MLM2894631211","MLM2894618113"]
for iid in ITEMS:
    print(f"\n=== {iid} ===")
    rd = requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,timeout=15)
    print(f"  GET desc: {rd.status_code}")
    d = rd.json() if rd.status_code == 200 else {}
    txt = d.get("plain_text") or d.get("text") or ""
    print(f"  longitud: {len(txt)}")
    print(f"  preview: {txt[:300]!r}")
