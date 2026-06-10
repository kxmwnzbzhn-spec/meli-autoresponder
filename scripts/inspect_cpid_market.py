import os, requests, json
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
import time
for attempt in range(6):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(8)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

CPID="MLM34280293"
cp=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=15).json()
print(f"=== {CPID} ===")
print("name:",cp.get("name"))
print("status:",cp.get("status"))
print("buy_box_winner:",cp.get("buy_box_winner"))
print("domain:",cp.get("domain_id"),"category:",cp.get("category_id"))
for a in cp.get("attributes",[])[:25]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
pics=cp.get("pictures") or []
print(f"pictures: {len(pics)}")
for p in pics[:3]: print("  ",p.get("url"))

# Items competing
i=requests.get(f"https://api.mercadolibre.com/products/{CPID}/items?limit=50",headers=H,timeout=20).json()
print(f"\nitems total: {i.get('paging',{}).get('total')}")
results=i.get("results") or []
prices_active=[]
for r in results[:25]:
  p=r.get("price"); st=r.get("status"); sold=r.get("sold_quantity")
  ml=r.get("listing_type_id"); cid=r.get("catalog_listing")
  pr=r.get("item_id") or r.get("id")
  print(f"  {pr} | ${p} | {st} | sold={sold} | type={ml} | catalog={cid}")
  if p and st=="active": prices_active.append(p)
if prices_active:
  prices_active.sort()
  print(f"\nactive sorted: {prices_active[:15]}")
  med=prices_active[len(prices_active)//2]
  print(f"min/median/max: ${prices_active[0]} / ${med} / ${prices_active[-1]}")

# Search by name
nm=cp.get("name") or ""
if nm:
  q=requests.utils.quote(nm)
  s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&limit=20",headers=H,timeout=15).json()
  res=s.get("results") or []
  sprices=sorted([r.get("price") for r in res if r.get("price")])
  print(f"\nMLM search '{nm[:70]}' total: {s.get('paging',{}).get('total')}")
  for r in res[:10]:
    print(f"  ${r.get('price')} | sold={r.get('sold_quantity')} | {r.get('title')[:80]}")
  if sprices:
    print(f"search min/median/max: ${sprices[0]} / ${sprices[len(sprices)//2]} / ${sprices[-1]}")
