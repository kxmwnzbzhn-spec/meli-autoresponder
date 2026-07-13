import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=["MLM5705924442","MLM3129625701","MLM5705923808","MLM5705934154",
       "MLM3129625793","MLM3129625781","MLM3129625757"]

for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,title",headers=H,timeout=10).json()
    before=g.get("status")
    title=(g.get("title") or "?")[:50]
    # Pause first
    if before=="active":
        pr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=10).json()
        paused=pr.get("status")
    else:
        paused=before
    # Close
    cr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=10).json()
    closed=cr.get("status")
    err=cr.get("error","")
    print(f"{iid} {before} -> paused:{paused} -> closed:{closed} err={err} | {title}",flush=True)
