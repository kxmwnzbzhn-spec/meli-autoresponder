import requests, json, sys
CPID="MLM34280293"
cp=requests.get(f"https://api.mercadolibre.com/products/{CPID}",timeout=15).json()
print(f"=== {CPID} ===")
print("name:",cp.get("name"))
print("status:",cp.get("status"))
print("buy_box_winner price:",(cp.get("buy_box_winner") or {}).get("price"))
print("domain:",cp.get("domain_id"),"category:",cp.get("category_id"))
for a in cp.get("attributes",[])[:25]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
pics=cp.get("pictures") or []
print(f"pictures: {len(pics)}")
print(f"main_features: {cp.get('main_features')}")

# Get list of competing items for the CPID
print("\n=== ITEMS COMPETING ON THIS CPID ===")
i=requests.get(f"https://api.mercadolibre.com/products/{CPID}/items?limit=50",timeout=20).json()
results=i.get("results") or []
print(f"total items: {i.get('paging',{}).get('total')}")
prices=[]
for r in results[:20]:
  p=r.get("price"); st=r.get("status"); sold=r.get("sold_quantity"); sid=r.get("seller_id"); sn=r.get("shipping",{}).get("free_shipping")
  pr=r.get("item_id") or r.get("id")
  print(f"  {pr} | ${p} | {st} | sold={sold} | seller={sid} | free_ship={sn}")
  if p and st=="active": prices.append(p)
if prices:
  prices.sort()
  print(f"\nactive prices (sorted): {prices[:10]}")
  print(f"min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")

# Search by name in MLM general
nm=cp.get("name") or ""
if nm:
  q=requests.utils.quote(nm)
  s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&limit=20",timeout=15).json()
  res=s.get("results") or []
  sprices=[r.get("price") for r in res if r.get("price")]
  sprices.sort()
  print(f"\n=== MLM SEARCH '{nm[:60]}' ===")
  print(f"total: {s.get('paging',{}).get('total')}")
  for r in res[:10]:
    print(f"  ${r.get('price')} | sold={r.get('sold_quantity')} | {r.get('title')[:70]}")
  if sprices:
    print(f"search min/median/max: ${sprices[0]} / ${sprices[len(sprices)//2]} / ${sprices[-1]}")
