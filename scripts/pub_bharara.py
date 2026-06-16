import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
CAT="MLM5686"
a=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
required=[]
for x in a:
  tags=x.get("tags",{}) or {}
  if tags.get("required") or tags.get("catalog_required") or tags.get("hidden")==False:
    required.append({"id":x.get("id"),"name":x.get("name"),"value_type":x.get("value_type"),"required":bool(tags.get("required"))})
for r in required:
  print(r)
print(f"\ntotal attrs: {len(a)}")
