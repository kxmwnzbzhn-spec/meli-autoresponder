import os, requests, json, time, urllib.parse
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}

CPID="MLM42230166"
print(f"=== {CPID} ===")
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"name: {cp.get('name')}")
print(f"buy_box: {cp.get('buy_box_winner')}")
print(f"domain: {cp.get('domain_id')} pdp_types: {cp.get('pdp_types')}")
for a in cp.get("attributes",[])[:10]:
  print(f"  {a.get('id')}: {a.get('value_name')}")

# Items competing
i=requests.get(f"{API}/products/{CPID}/items?limit=50",headers=H,timeout=20).json()
total=i.get("paging",{}).get("total")
print(f"\nitems en CPID: total={total}")
prices=[]
for r2 in i.get("results",[])[:25]:
  p=r2.get("price"); st=r2.get("status"); sold=r2.get("sold_quantity"); ml=r2.get("listing_type_id")
  iid=r2.get("item_id") or r2.get("id")
  print(f"  {iid} | ${p} | {st} | sold={sold} | {ml}")
  if p and st=="active": prices.append(p)
prices.sort()
if prices:
  print(f"\nactive min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")

# Search free-text
print(f"\n=== SEARCH 'Marshall Emberton' ===")
q=urllib.parse.quote("Marshall Emberton bocina bluetooth")
s=requests.get(f"{API}/sites/MLM/search?q={q}&limit=20",headers=H,timeout=15).json()
sp=[]
for r2 in (s.get("results") or [])[:15]:
  p=r2.get("price"); ti=(r2.get("title") or "")[:75]
  print(f"  ${p} | {ti}")
  if p: sp.append(p)
sp.sort()
if sp:
  print(f"\nsearch min/median/max: ${sp[0]} / ${sp[len(sp)//2]} / ${sp[-1]}")
