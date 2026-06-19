import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

IDS="""2945250605 2967805775 2967759907 2967805695 2967759935 2967805753 2967785553 2605081655 2967759915 2967785655 2967805717 2967759903 2967772777 2967772767 2967772817 2967805759 2945214721 2699958881 2967772829 2592360377 2594259089""".split()
IIDS=[f"MLM{x}" for x in dict.fromkeys(IDS)]
print(f"unique: {len(IIDS)}")

ACCOUNTS=[("AH","MELI_REFRESH_TOKEN_AH"),("WILBERT","MELI_REFRESH_TOKEN_WILBERT")]
TOKENS={}
for n,k in ACCOUNTS:
  rt=os.environ.get(k)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20)
  if r.status_code<400: TOKENS[n]=r.json()["access_token"]; print(f"  ✓ {n}")

results={}
for IID in IIDS:
  hit=None
  for name,AT in TOKENS.items():
    H={"Authorization":f"Bearer {AT}"}
    HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,sub_status,available_quantity",headers=H,timeout=15)
    if g.status_code==200:
      hit=(name,AT,HJ,g.json()); break
  if not hit:
    print(f"\n{IID}: not accessible by any account")
    results[IID]={"account":None,"status":"not_found"}
    continue
  name,AT,HJ,info=hit
  print(f"\n{IID} ({name}): pre status={info.get('status')} sub={info.get('sub_status')} qty={info.get('available_quantity')} price={info.get('price')}")
  # Sequence of actions
  for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
    p=requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status,available_quantity",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
  print(f"  POST: status={g2.get('status')} sub={g2.get('sub_status')}")
  results[IID]={"account":name,"title":info.get("title"),"final_status":g2.get("status"),"sub":g2.get("sub_status")}

print("\n\n=== SUMMARY ===")
for iid,r in results.items():
  print(f"  {iid} | {r.get('account')} | {r.get('final_status','?')} | {r.get('title','')[:50] if r.get('title') else r.get('status','')}")
