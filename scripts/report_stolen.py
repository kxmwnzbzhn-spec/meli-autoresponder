import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for cid in [5530358522,5530353540]:
  c=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=20).json()
  print(f"\n=== CLAIM {cid} ===")
  print("stage:",c.get("stage"),"status:",c.get("status"),"sub:",c.get("status_detail"),"resolution:",c.get("resolution"))
  print("type:",c.get("type"),"reason:",c.get("reason_id"))
  print("players:",[(p.get("role"),p.get("type"),p.get("available_actions",[])) for p in c.get("players",[])])
  # try actions endpoint
  a=requests.get(f"{API}/post-purchase/v1/claims/{cid}/players/respondent",headers=H,timeout=20)
  print("respondent actions:",a.status_code,a.text[:400])
