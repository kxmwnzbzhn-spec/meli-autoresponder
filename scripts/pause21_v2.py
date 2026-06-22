import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

ACC={"AH":"MELI_REFRESH_TOKEN_AH","ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","WILBERT":"MELI_REFRESH_TOKEN_WILBERT","JUAN":"MELI_REFRESH_TOKEN_JUAN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO","MAYRELY":"MELI_REFRESH_TOKEN_MAYRELY","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW","ADRIAN":"MELI_REFRESH_TOKEN_ADRIAN","ANGEL":"MELI_REFRESH_TOKEN_ANGEL","ASGARI":"MELI_REFRESH_TOKEN_ASGARI","MC":"MELI_REFRESH_TOKEN_MC"}

ORDER_ID="2000013579459581"
for n,k in ACC.items():
  rt=os.environ.get(k)
  if not rt: continue
  try:
    tr=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20)
    if tr.status_code>=400: continue
    AT=tr.json()["access_token"]
    g=requests.get(f"{API}/orders/{ORDER_ID}",headers={"Authorization":f"Bearer {AT}"},timeout=15)
    if g.status_code==200 and g.json().get("total_amount"):
      info=g.json()
      print(f"✓ {n}: total=${info.get('total_amount')} buyer={info.get('buyer',{}).get('nickname')} status={info.get('status')}")
      # Probe claims
      cs=requests.get(f"{API}/post-purchase/v1/claims/search?resource=order&resource_id={ORDER_ID}",headers={"Authorization":f"Bearer {AT}"},timeout=15)
      print(f"  claims: {cs.status_code} {cs.text[:600]}")
      # Also try seller claims search
      cs2=requests.get(f"{API}/post-purchase/v1/claims/search?status=opened&player.role=respondent&limit=100",headers={"Authorization":f"Bearer {AT}"},timeout=15)
      if cs2.status_code==200:
        for c in cs2.json().get("data") or cs2.json().get("results") or []:
          if str(c.get("resource_id")) == ORDER_ID:
            print(f"  FOUND CLAIM: {c.get('id')} stage={c.get('stage')}")
      break
    else:
      print(f"✗ {n}: HTTP {g.status_code}")
  except Exception as e: print(f"  {n} err: {e}")
