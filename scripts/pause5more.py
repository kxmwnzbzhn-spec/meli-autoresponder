import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

IIDS=["MLM2967785667","MLM2967805739","MLM2967772809","MLM2967785571","MLM2592740671"]
ACCOUNTS={"AH":"MELI_REFRESH_TOKEN_AH","ASVA":"MELI_REFRESH_TOKEN_ASVA","JUAN":"MELI_REFRESH_TOKEN_JUAN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO","WILBERT":"MELI_REFRESH_TOKEN_WILBERT","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW"}
TOKENS={}
for n,k in ACCOUNTS.items():
  rt=os.environ.get(k)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  if r.status_code<400: TOKENS[n]=r.json()["access_token"]
print(f"tokens: {list(TOKENS.keys())}")

results={}
for IID in IIDS:
  hit=None
  for name,AT in TOKENS.items():
    g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,seller_id",headers={"Authorization":f"Bearer {AT}"},timeout=15)
    if g.status_code==200: hit=(name,AT,g.json()); break
  if not hit: print(f"{IID}: not accessible"); results[IID]=None; continue
  name,AT,info=hit
  HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  print(f"\n{IID} ({name}): {info.get('title','')[:50]} ${info.get('price')} {info.get('status')}")
  for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
    requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
  print(f"  → {g2.get('status')} {g2.get('sub_status')}")
  results[IID]={"acct":name,"title":info.get("title"),"price":info.get("price"),"final":g2.get("status")}

print("\n=== SUMMARY ===")
for iid,r in results.items():
  if r: print(f"  {iid} | {r['acct']} | {r['final']} | {r['title'][:50]}")
