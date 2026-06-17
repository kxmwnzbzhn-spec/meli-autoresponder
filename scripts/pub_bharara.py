import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CAT="MLM194118"; IID="MLM3025719815"
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
g=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
current={a["id"]:(a.get("value_name") or a.get("value_id")) for a in g.get("attributes",[])}
filled_ids={k for k,v in current.items() if v}
print(f"category attrs: {len(ats)}")
print(f"currently filled: {len(filled_ids)}")
print(f"empty attrs to address: {len([a for a in ats if a['id'] not in filled_ids])}\n")

# Dump every empty attr with its schema
for a in ats:
  if a["id"] in filled_ids: continue
  print(f"  {a['id']:30s} | name='{a.get('name')}' type={a.get('value_type')}")
  vs=a.get("values") or []
  if vs:
    sample=", ".join(v.get("name","") for v in vs[:5])
    print(f"      sample values: {sample}")
