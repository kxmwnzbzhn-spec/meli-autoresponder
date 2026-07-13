import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=[
    ("MLM5608963102","Oud Wood"),
    ("MLM5608966150","Chocolate"),
    ("MLM5608969058","Bacarat"),
    ("MLM3066668067","Salvaje Elixir"),
    ("MLM3066669563","Mango"),
    ("MLM3066762263","Orquídea Negra"),
    ("MLM5609034818","Leche de Coco"),
    ("MLM3066811803","Roma Royale"),
    ("MLM5609248742","Vainilla y Tabaco"),
    ("MLM5609025076","Bubble Gum"),
    ("MLM3066668603","Aventura"),
    ("MLM5608898232","Santal"),
]
for iid, name in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
    before=g.get("status")
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
    after=r.get("status")
    err=r.get("error","")
    print(f"{iid} ({name}) {before} -> {after} err={err}",flush=True)
