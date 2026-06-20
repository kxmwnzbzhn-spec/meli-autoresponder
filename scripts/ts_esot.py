import os, requests, json
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
# attributes endpoint da values con id
r=requests.get(f"{API}/categories/MLM456032/attributes",headers=H,timeout=20)
print("status",r.status_code)
data=r.json() if r.status_code==200 else []
for a in data:
    aid=a.get("id"); name=a.get("name"); tg=a.get("tags") or {}
    req = (isinstance(tg,dict) and (tg.get("required") or tg.get("catalog_required"))) or (isinstance(tg,list) and ("required" in tg or "catalog_required" in tg))
    if req or aid in ('BRAND','LINE','MODEL','PERFUME_NAME','SCENT','GENDER','PERFUME_TYPE','UNIT_VOLUME','GTIN','ITEM_CONDITION','OLFACTORY_FAMILIES','APPLICATION_FORMAT'):
        print(f"\n[{aid}] {name} tags={tg}")
        for v in (a.get("values") or [])[:25]:
            print("   -", v.get("name"), "id=", v.get("id"))
