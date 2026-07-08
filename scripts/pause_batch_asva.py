import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=["MLM2886030837","MLM5233480022","MLM3066033037","MLM3066095021",
       "MLM5607789818","MLM5576391292","MLM3049333265","MLM5656253306"]

for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,available_quantity,title",headers=H,timeout=10).json()
    before=g.get("status")
    title=g.get("title","?")[:50]
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
    after=r.get("status")
    err=r.get("error","")
    print(f"{iid} {before} -> {after} err={err} | {title}",flush=True)
