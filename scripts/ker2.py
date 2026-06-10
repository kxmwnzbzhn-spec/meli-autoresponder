import os, requests, urllib.parse
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; print(f"[ROTATED RT] {tok['refresh_token']}")
H={"Authorization":f"Bearer {AT}"}

# Search by hair_fixatives domain
for q in ["Kerastase Elixir Ultime","Kerastase aceite","aceite kerastase 100","aceite capilar kerastase"]:
  qe=urllib.parse.quote(q)
  for url in [f"https://api.mercadolibre.com/sites/MLM/search?q={qe}&limit=15",
              f"https://api.mercadolibre.com/sites/MLM/search?q={qe}&category=MLM166700&limit=15"]:
    try:
      s=requests.get(url,timeout=15)
      js=s.json()
      res=js.get("results") or []
      print(f"\n=== '{q}' url={url[-60:]} status={s.status_code} total={js.get('paging',{}).get('total')} results={len(res)} ===")
      prices=[]
      for r2 in res[:12]:
        p=r2.get("price"); sold=r2.get("sold_quantity"); cond=r2.get("condition")
        print(f"  ${p} | sold={sold} | cond={cond} | {(r2.get('title') or '')[:75]}")
        if p: prices.append(p)
      if prices:
        prices.sort()
        print(f"  min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")
    except Exception as e:
      print(f"  err: {e}")
