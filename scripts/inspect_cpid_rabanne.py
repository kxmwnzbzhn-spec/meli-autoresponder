import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}
CPID="MLM51198714"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"name: {cp.get('name')}")
for a in cp.get("attributes",[])[:20]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
pics=cp.get("pictures") or []
print(f"pictures: {len(pics)}")
for p in pics[:5]: print(f"  {p.get('url')}")
