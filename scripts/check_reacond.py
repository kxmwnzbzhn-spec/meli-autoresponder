import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IDS=["MLM5223653312","MLM2880875395","MLM5223547812","MLM2880875381","MLM2880875423"]
print("=== Reacond Go4 status ===")
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    ss=it.get("sub_status") or []
    ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
    price=it.get("price")
    print(f"{iid} | {it.get('status')}/{ss_str} | ${price} | {it.get('title','')[:60]}")
    # Si está en under_review o paused, intentar cambiar precio y activar
    if price != 499:
        rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":499},timeout=15)
        print(f"  price update: {rr.status_code}")
    if it.get("status") in ("paused","under_review"):
        rr=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=15)
        print(f"  activate: {rr.status_code} {rr.text[:100] if rr.status_code>=400 else 'OK'}")
