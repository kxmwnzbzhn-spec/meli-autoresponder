import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

for cid in [5530358522,5530353540]:
  print(f"\n=== CLAIM {cid} ===")
  # Get return associated
  for p in [
    f"/post-purchase/v1/claims/{cid}/related/return",
    f"/post-purchase/v1/claims/{cid}/returns",
    f"/post-purchase/v1/claims/{cid}/related_entities",
    f"/post-purchase/v2/claims/{cid}/related/return",
    f"/post-purchase/v1/claims/{cid}/return",
    f"/marketplace/v2/claims/{cid}/returns",
    f"/marketplace/v1/claims/{cid}/returns",
  ]:
    rr=requests.get(f"{API}{p}",headers=HJ,timeout=15)
    if rr.status_code not in (404,):
      print(f"  GET {p} {rr.status_code} {rr.text[:600]}")
