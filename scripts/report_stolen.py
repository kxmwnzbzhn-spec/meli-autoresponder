import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Probe many shape variants for the action with EMPTY body first
for cid in [5530358522]:
  for path in [
    f"/post-purchase/v1/claims/{cid}/actions/return_review_fail",
    f"/post-purchase/v1/claims/{cid}/actions/return_review_unified_fail",
    f"/post-purchase/v1/claims/{cid}/players/respondent/actions/return_review_fail",
    f"/post-purchase/v1/claims/{cid}/players/respondent/actions/return_review_unified_fail",
    f"/marketplace/v1/claims/{cid}/players/respondent/actions/return_review_fail",
    f"/marketplace/v1/claims/{cid}/players/respondent/actions/return_review_unified_fail",
    f"/post-purchase/v2/claims/{cid}/players/respondent/actions/return_review_fail",
  ]:
    rr=requests.post(f"{API}{path}",headers=HJ,json={},timeout=15)
    if rr.status_code!=404:
      print(f"{path}\n  {rr.status_code} {rr.text[:300]}")
