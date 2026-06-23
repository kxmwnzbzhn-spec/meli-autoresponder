import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Full claim dump to see action structure
for cid in [5530358522]:
  c=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=HJ,timeout=20).json()
  print(json.dumps(c, indent=2, default=str)[:5000])
  # Try GET available actions
  print("\n--- /actions GET ---")
  a=requests.get(f"{API}/post-purchase/v1/claims/{cid}/actions",headers=HJ,timeout=15)
  print(a.status_code, a.text[:1500])
  print("\n--- /available_actions GET ---")
  a=requests.get(f"{API}/post-purchase/v1/claims/{cid}/available_actions",headers=HJ,timeout=15)
  print(a.status_code, a.text[:1500])
  print("\n--- /returns GET ---")
  a=requests.get(f"{API}/post-purchase/v1/claims/{cid}/returns/expected_resolutions",headers=HJ,timeout=15)
  print(a.status_code, a.text[:600])
