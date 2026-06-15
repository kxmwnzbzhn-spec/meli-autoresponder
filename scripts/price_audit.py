import os, requests, json, urllib.parse, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

# 1) CPID info + competing items
CPID="MLM51198714"
print(f"\n=== CPID {CPID} ===")
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"name: {cp.get('name')}")
print(f"buy_box_winner: {cp.get('buy_box_winner')}")

# Items competing on this CPID
i=requests.get(f"{API}/products/{CPID}/items?limit=50",headers=H,timeout=20).json()
total=i.get("paging",{}).get("total")
results=i.get("results",[])
print(f"items en CPID: total={total}")
active_prices=[]
for r2 in results[:25]:
  p=r2.get("price"); st=r2.get("status"); sold=r2.get("sold_quantity"); ml=r2.get("listing_type_id")
  iid=r2.get("item_id") or r2.get("id")
  print(f"  {iid} | ${p} | {st} | sold={sold} | {ml}")
  if p and st=="active": active_prices.append(p)
if active_prices:
  active_prices.sort()
  print(f"\nactive sorted: {active_prices}")
  print(f"min: ${active_prices[0]} | median: ${active_prices[len(active_prices)//2]} | max: ${active_prices[-1]}")

# 2) Free-text search MLM
print(f"\n=== SEARCH MLM 'Rabanne 1 Million Gold Elixir 100ml' ===")
q=urllib.parse.quote("Rabanne 1 Million Gold Elixir 100ml")
s=requests.get(f"{API}/sites/MLM/search?q={q}&limit=30",headers=H,timeout=15).json()
total_s=s.get("paging",{}).get("total")
print(f"total search: {total_s}")
prices=[]
for r2 in (s.get("results") or [])[:20]:
  p=r2.get("price"); sold=r2.get("sold_quantity"); cond=r2.get("condition")
  ti=(r2.get("title") or "")[:80]
  print(f"  ${p} | sold={sold} | {cond} | {ti}")
  if p: prices.append(p)
if prices:
  prices.sort()
  print(f"\nsearch sorted: {prices[:15]}")
  print(f"search min: ${prices[0]} | median: ${prices[len(prices)//2]} | max: ${prices[-1]}")

# 3) Pacto Rabanne otros (1 Million general) para tener referencia
print(f"\n=== SEARCH 'Rabanne 1 Million Parfum 100ml' (línea general) ===")
q2=urllib.parse.quote("Rabanne 1 Million Parfum 100ml")
s2=requests.get(f"{API}/sites/MLM/search?q={q2}&limit=20",headers=H,timeout=15).json()
prices2=[]
for r2 in (s2.get("results") or [])[:15]:
  p=r2.get("price")
  if p: prices2.append(p)
if prices2:
  prices2.sort()
  print(f"  range: ${prices2[0]} – ${prices2[-1]}  median: ${prices2[len(prices2)//2]}")
