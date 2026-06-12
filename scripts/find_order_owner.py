import os, requests, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
ORDER="2000013323144453"

ACCS=[
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
  ("YC_NEW","MELI_REFRESH_TOKEN"),
]

# Also search as pack_id and other resources
for nick,sec in ACCS:
  rt=os.environ.get(sec)
  if not rt: continue
  try:
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
      "client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=12)
    if r.status_code>=300: continue
    AT=r.json()["access_token"]
    H={"Authorization":f"Bearer {AT}"}
    # As order
    g=requests.get(f"{API}/orders/{ORDER}",headers=H,timeout=8)
    # Search via packs
    p=requests.get(f"{API}/packs/{ORDER}",headers=H,timeout=8)
    # Search claims by pack
    cp=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,
      params={"pack_id":ORDER,"limit":5},timeout=8)
    cd=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,
      params={"order_id":ORDER,"limit":5},timeout=8)
    if g.status_code==200 or p.status_code==200 or (cp.status_code==200 and cp.json().get('paging',{}).get('total',0)>0) or (cd.status_code==200 and cd.json().get('paging',{}).get('total',0)>0):
      print(f">>> {nick}: order_get={g.status_code} pack_get={p.status_code} claims_by_pack={cp.json().get('paging',{}).get('total',0) if cp.status_code==200 else 'err'} claims_by_order={cd.json().get('paging',{}).get('total',0) if cd.status_code==200 else 'err'}")
      if g.status_code==200:
        od=g.json()
        print(f"    title: {(od.get('order_items') or [{}])[0].get('item',{}).get('title','')[:80]}")
      if p.status_code==200:
        pd=p.json()
        print(f"    pack orders: {[o.get('id') for o in pd.get('orders',[])]}")
    else:
      print(f"  {nick}: not here")
  except Exception as e:
    print(f"  {nick}: err {e}")
