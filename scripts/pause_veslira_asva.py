import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=["MLM5608963106","MLM5608963102","MLM5608903488","MLM5608966150",
       "MLM5608906516","MLM5608969058","MLM5609032438","MLM3066668067",
       "MLM3066634979","MLM3066669563","MLM5609246298","MLM3066762263",
       "MLM3066670419","MLM5609034818","MLM5609357580","MLM3066811803",
       "MLM5609237578","MLM5609248742","MLM5608964362","MLM5609025076",
       "MLM3066679097","MLM3066668603"]

for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
    before=g.get("status")
    if before=="active":
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
        after=r.get("status")
        err=r.get("message","")
    else:
        after=before
        err=""
    print(f"{iid} {before} -> {after} err={err}",flush=True)
    time.sleep(0.3)
