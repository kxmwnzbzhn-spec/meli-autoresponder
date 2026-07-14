import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=["MLM3129625691","MLM3130262123","MLM3129626365","MLM5705924478",
       "MLM5705924474","MLM5705924452","MLM3129625715"]

for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status,price,title",headers=H,timeout=10).json()
    price=g.get("price") or 0
    title=(g.get("title") or "?")[:50]
    if price>499:
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":499},timeout=15).json()
        if r.get("error"):
            print(f"{iid} ${price} -> FAIL: {r.get('message','?')[:100]} | {title}",flush=True)
        else:
            print(f"{iid} ${price} -> $499 ✅ | {title}",flush=True)
    else:
        print(f"{iid} ${price} (ya OK) | {title}",flush=True)
    time.sleep(0.3)
