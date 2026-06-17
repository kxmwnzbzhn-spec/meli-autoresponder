import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Re-snap competitor and undercut to one peso below the cheapest
IID="MLM5511720082"
CPID="MLM44709174"
FLOOR=299

i=requests.get(f"{API}/products/{CPID}/items?limit=30",headers=H,timeout=15).json()
ours_price=None; others=[]
for r2 in (i.get("results") or []):
  iid=r2.get("item_id"); p=r2.get("price")
  if not p: continue
  if iid==IID: ours_price=p
  else: others.append((p,iid))
others.sort()
print(f"ours: ${ours_price}")
print(f"cheapest competitor: ${others[0][0] if others else 'none'} ({others[0][1] if others else ''})")

target=max(FLOOR, int(others[0][0])-1) if others else ours_price
print(f"target: ${target}")
if target != ours_price:
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":target},timeout=20)
  print(f"PUT price {target}: {p.status_code}")
  print(p.text[:400])

g=requests.get(f"{API}/items/{IID}?attributes=id,price,status",headers=H,timeout=15).json()
print(f"\nnow: {g}")
