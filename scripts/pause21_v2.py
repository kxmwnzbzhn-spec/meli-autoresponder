import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

ACC={"AH":"MELI_REFRESH_TOKEN_AH","ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL",
     "WILBERT":"MELI_REFRESH_TOKEN_WILBERT","JUAN":"MELI_REFRESH_TOKEN_JUAN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
     "MAYRELY":"MELI_REFRESH_TOKEN_MAYRELY","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW","ADRIAN":"MELI_REFRESH_TOKEN_ADRIAN",
     "ANGEL":"MELI_REFRESH_TOKEN_ANGEL","ASGARI":"MELI_REFRESH_TOKEN_ASGARI","MC":"MELI_REFRESH_TOKEN_MC",
     "OFICIAL":"MELI_REFRESH_TOKEN_OFICIAL","USER1668":"MELI_REFRESH_TOKEN_USER1668","RAYMUNDO_MAY":"MELI_REFRESH_TOKEN_RAYMUNDO_MAY",
     "RMAYCHI":"MELI_REFRESH_TOKEN_RMAYCHI","BREN":"MELI_REFRESH_TOKEN_BREN","MILDRED":"MELI_REFRESH_TOKEN_MILDRED",
     "DILCIE":"MELI_REFRESH_TOKEN_DILCIE","ANGEL_DAMIAN":"MELI_REFRESH_TOKEN_ANGEL_DAMIAN"}

ORDERS=["2000013543063645","2000013543121015"]
TOKENS={}
for n,k in ACC.items():
  rt=os.environ.get(k)
  if not rt: continue
  try:
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=15)
    if r.status_code<400: TOKENS[n]=r.json()["access_token"]
  except: pass

for ORD in ORDERS:
  print(f"\n=== {ORD} ===")
  for n,AT in TOKENS.items():
    try:
      g=requests.get(f"{API}/orders/{ORD}",headers={"Authorization":f"Bearer {AT}"},timeout=10)
      if g.status_code==200 and g.json().get("total_amount"):
        info=g.json()
        print(f"  ✓ {n}: total=${info.get('total_amount')} status={info.get('status')} buyer={info.get('buyer',{}).get('nickname')}")
        for it in info.get("order_items",[]):
          print(f"    {it.get('item',{}).get('title','')[:60]} x{it.get('quantity')}")
        break
    except: pass
  else:
    print(f"  ✗ not found in any of {len(TOKENS)} accounts")
