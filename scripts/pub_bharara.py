import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

iid="MLM5525982716"
g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
print(f"=== Item {iid} attributes ({len(g.get('attributes',[]))} total) ===")
empty=0
for a in g.get("attributes",[]):
  v=a.get("value_name")
  if not v: empty+=1
  print(f"  {a.get('id'):30s} = {v}")
print(f"\nempty: {empty}")

# Get the spec to identify recommended/required + valid values
print("\n=== MAIN_COLOR allowed values in MLM59800 ===")
ats=requests.get(f"{API}/categories/MLM59800/attributes",headers=H,timeout=15).json()
for a in ats:
  if a.get("id")=="MAIN_COLOR":
    print(f"  required: {a.get('tags',{}).get('required')}")
    print(f"  value_type: {a.get('value_type')}")
    for v in (a.get("values") or [])[:30]:
      print(f"    {v.get('id')}: {v.get('name')}")
    break

# Required + catalog_required attrs not filled
print("\n=== Required/Recommended attrs in category ===")
current_ids=set(a.get("id") for a in g.get("attributes",[]) if a.get("value_name"))
missing_req=[]
for a in ats:
  tags=a.get("tags",{}) or {}
  if (tags.get("required") or tags.get("catalog_required")) and a.get("id") not in current_ids:
    missing_req.append(a.get("id"))
print(f"missing required: {missing_req}")
