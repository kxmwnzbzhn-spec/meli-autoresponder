import os, requests, urllib.parse
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
import time
for attempt in range(5):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; print(f"[ROTATED RT] {tok['refresh_token']}")
H={"Authorization":f"Bearer {AT}"}

for q in ["Kerastase Elixir Ultime 100","Kerastase Elixir Ultime","Kerastase fijador 100ml"]:
  qe=urllib.parse.quote(q)
  s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={qe}&limit=20",headers=H,timeout=15).json()
  res=s.get("results") or []
  total=s.get("paging",{}).get("total")
  print(f"\n=== '{q}' total={total} ===")
  prices=[]
  for r in res[:15]:
    p=r.get("price"); st=r.get("condition") or r.get("status"); sold=r.get("sold_quantity")
    print(f"  ${p} | sold={sold} | {st} | {(r.get('title') or '')[:80]}")
    if p: prices.append(p)
  if prices:
    prices.sort()
    print(f"  min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")
