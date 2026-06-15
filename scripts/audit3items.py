import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}

ITEMS=["MLM2969825393","MLM2969827221","MLM2969825239"]
for ITEM in ITEMS:
  print(f"\n{'='*60}\nITEM {ITEM}\n{'='*60}")
  g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=12).json()
  print(f"title: {g.get('title')}")
  print(f"price: ${g.get('price')}  status: {g.get('status')}  qty: {g.get('available_quantity')}")
  CPID=g.get("catalog_product_id")
  print(f"CPID: {CPID}")
  # If no CPID, find one via product matching (search by GTIN or title)
  if CPID:
    cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
    print(f"  cpid_name: {cp.get('name')}")
    bb=cp.get("buy_box_winner") or {}
    print(f"  buy_box_winner: ${bb.get('price')}  by_seller={bb.get('seller_id')}")
    # Items competing on CPID
    i=requests.get(f"{API}/products/{CPID}/items?limit=50",headers=H,timeout=15).json()
    res=i.get("results",[])
    print(f"  items en CPID: total={i.get('paging',{}).get('total')}")
    active_prices=[]
    for r2 in res[:20]:
      p=r2.get("price"); st=r2.get("status"); sold=r2.get("sold_quantity"); ml=r2.get("listing_type_id")
      iid=r2.get("item_id") or r2.get("id")
      print(f"    {iid} | ${p} | {st} | sold={sold} | {ml}")
      if p and st=="active": active_prices.append(p)
    if active_prices:
      active_prices.sort()
      print(f"  active sorted: {active_prices}")
      print(f"  min/median/max: ${active_prices[0]} / ${active_prices[len(active_prices)//2]} / ${active_prices[-1]}")
  else:
    print("  (tradicional sin CPID - usar título + BRAND para buscar competidores)")
    # Use search by title (top words)
    import urllib.parse
    title_words=g.get("title","").split()[:5]
    q=urllib.parse.quote(" ".join(title_words))
    s=requests.get(f"{API}/sites/MLM/search?q={q}&limit=20",headers=H,timeout=15).json()
    prices=[]
    for r2 in (s.get("results") or [])[:15]:
      p=r2.get("price")
      ti=(r2.get("title") or "")[:80]
      if p:
        prices.append(p)
        print(f"    ${p} | {ti}")
    if prices:
      prices.sort()
      print(f"  market sorted: {prices[:10]}")
      print(f"  min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")
