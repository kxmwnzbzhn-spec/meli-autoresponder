import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
g=requests.get(f"{API}/items/MLM2976325463",headers=H,timeout=12).json()
print(f"Time: {time.strftime('%H:%M:%S')}")
for v in g.get("variations",[]):
  for ac in v.get("attribute_combinations",[]):
    if ac.get("id")=="SIZE":
      print(f"  size={ac.get('value_name')} qty={v.get('available_quantity')}")
