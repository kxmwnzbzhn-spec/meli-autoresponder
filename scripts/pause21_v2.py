import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

IIDS="""MLM2945250605 MLM2967805775 MLM2967759907 MLM2967805695 MLM2967759935 MLM2967805753 MLM2967785553 MLM2605081655 MLM2967759915 MLM2967785655 MLM2967805717 MLM2967759903 MLM2967772777 MLM2967772767 MLM2967772817 MLM2967805759 MLM2945214721 MLM2699958881 MLM2967772829 MLM2592360377 MLM2594259089""".split()

ACCOUNTS={
  "AH":"MELI_REFRESH_TOKEN_AH",
  "ASVA":"MELI_REFRESH_TOKEN_ASVA",
  "JUAN":"MELI_REFRESH_TOKEN_JUAN",
  "RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
  "WILBERT":"MELI_REFRESH_TOKEN_WILBERT",
  "CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL",
  "DILCIE":"MELI_REFRESH_TOKEN_DILCIE",
  "BREN":"MELI_REFRESH_TOKEN_BREN",
  "MILDRED":"MELI_REFRESH_TOKEN_MILDRED",
  "YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW",
  "MG20260424":"MELI_REFRESH_TOKEN_MG20260424",
}
TOKENS={}
for n,k in ACCOUNTS.items():
  rt=os.environ.get(k)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  if r.status_code<400:
    TOKENS[n]=r.json()["access_token"]
print(f"tokens loaded: {list(TOKENS.keys())}")

results={}
for IID in IIDS:
  hit=None
  for name,AT in TOKENS.items():
    H={"Authorization":f"Bearer {AT}"}
    g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,sub_status,available_quantity,seller_id",headers=H,timeout=15)
    if g.status_code==200:
      hit=(name,AT,g.json()); break
  if not hit:
    print(f"{IID}: NOT accessible by any of {len(TOKENS)} tokens")
    results[IID]={"acct":None}
    continue
  name,AT,info=hit
  HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
  print(f"\n{IID} ({name}, seller={info.get('seller_id')}): {info.get('title','')[:50]} ${info.get('price')} status={info.get('status')}")
  for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
    p=requests.put(f"{API}/items/{IID}",headers=HJ,json=action,timeout=20)
  g2=requests.get(f"{API}/items/{IID}?attributes=id,status,sub_status",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
  print(f"  → {g2.get('status')} {g2.get('sub_status')}")
  results[IID]={"acct":name,"title":info.get("title"),"final":g2.get("status"),"sub":g2.get("sub_status")}

print("\n=== SUMMARY ===")
ok=sum(1 for r in results.values() if r.get("final") in ("closed","paused"))
ng=sum(1 for r in results.values() if not r.get("acct"))
print(f"OK: {ok}/{len(IIDS)}, not_found: {ng}")

# Also collect by account for supabase update
acct_map={}
for iid,r in results.items():
  if r.get("acct"):
    acct_map.setdefault(r["acct"],[]).append(iid)
for acct,items in acct_map.items():
  print(f"  {acct}: {len(items)} items")
