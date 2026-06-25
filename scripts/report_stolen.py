import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Get current item
it=requests.get(f"{API}/items/MLM3035212177",headers=HJ,timeout=15).json()
print("status_before:",it.get("status"))

# Ensure active
if it.get("status")!="active":
  rr=requests.put(f"{API}/items/MLM3035212177",headers=HJ,json={"status":"active"},timeout=20)
  print("activate:",rr.status_code,rr.text[:200])

# Set qty=1 for ALL 3 variants
vars_payload=[]
for v in (it.get("variations") or []):
  vars_payload.append({"id":v["id"],"available_quantity":1})
rr=requests.put(f"{API}/items/MLM3035212177",headers=HJ,json={"variations":vars_payload},timeout=25)
print(f"variants qty=1 PUT: {rr.status_code}")
# Verify
it2=requests.get(f"{API}/items/MLM3035212177",headers=HJ,timeout=15).json()
for v in (it2.get("variations") or []):
  size=next((a.get("value_name") for a in v.get("attribute_combinations",[]) if a.get("id")=="SIZE"),"?")
  print(f"  variant {v.get('id')} size={size} qty={v.get('available_quantity')}")
print("status_after:",it2.get("status"),"qty_total:",it2.get("available_quantity"))
