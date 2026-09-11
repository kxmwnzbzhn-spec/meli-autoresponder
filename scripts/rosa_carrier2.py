import os,json,requests
API="https://api.mercadolibre.com"; SELLER=3658310023
IDS=json.load(open("config/rosa_153_ids.json"))
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
# Probar varios endpoints para saber carrier
sid=IDS[0]
for path in [f"/shipments/{sid}/carrier", f"/shipments/{sid}/tracking", f"/shipments/{sid}/costs", f"/shipments/{sid}/lead_time"]:
 g=requests.get(f"{API}{path}",headers=H,timeout=15)
 print(f"\n### {path} → {g.status_code}\n{g.text[:600]}")
