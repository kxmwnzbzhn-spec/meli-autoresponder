import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IDS="""MLM3035113081 MLM3035329415 MLM3035214007 MLM3035214011 MLM3035329423 MLM3035239685 MLM3035239695 MLM3035113097 MLM3035239697 MLM3035329431 MLM3035113103 MLM3035113107 MLM3035329433 MLM3035239701 MLM3035239707 MLM3035113121 MLM3035329439 MLM3035329441 MLM3035113127 MLM3035239719 MLM3035239723 MLM3035239727 MLM3035329451 MLM3035214041 MLM3035239733 MLM3035113143 MLM3035329459 MLM3035113157 MLM3035239741 MLM3035113159 MLM3035214059 MLM3035214061 MLM3035113175""".split()
print(f"items: {len(IDS)}")

ok=0; fail=0
for IID in IDS:
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"available_quantity":1},timeout=20)
  if p.status_code<400: 
    ok+=1; print(f"  ✓ {IID}")
  else: 
    fail+=1; print(f"  ✗ {IID}: {p.status_code} {p.text[:200]}")
  time.sleep(0.2)
print(f"\nDONE: ok={ok} fail={fail}/{len(IDS)}")
