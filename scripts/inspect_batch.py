import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
IDS=["MLM2969839267","MLM2969839197","MLM2969839167","MLM2969825393","MLM2969851519"]
for iid in IDS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"\n=== {iid} ===")
    print(f"title: {g.get('title')}")
    print(f"price: {g.get('price')}")
    print(f"pictures: {len(g.get('pictures') or [])}")
    attrs={a.get('id'):a.get('value_name') for a in (g.get('attributes') or [])}
    for k in ["BRAND","PERFUME_NAME","PERFUME_TYPE","UNIT_VOLUME","GENDER","MODEL","GTIN","ALPHANUMERIC_MODEL"]:
        if k in attrs: print(f"  {k}: {attrs[k]}")
