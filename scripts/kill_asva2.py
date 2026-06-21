import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Probe known esoteric category candidates
for c in ["MLM5286","MLM5285","MLM5277","MLM5279","MLM177670","MLM6111","MLM6112","MLM177601","MLM6003","MLM6005","MLM177672","MLM3937"]:
  try:
    r=requests.get(f"{API}/categories/{c}",headers=H,timeout=8).json()
    if r.get("name"):
      path=" > ".join(p.get("name") for p in r.get("path_from_root",[]))
      kids=len(r.get("children_categories",[]))
      print(f"  {c}: {path} (children: {kids})")
  except: pass
