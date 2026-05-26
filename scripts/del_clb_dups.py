import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
# 3 tradicionales canibalizadoras
IDS=["MLM2888511079","MLM2888507597","MLM2888976949"]
for sid in IDS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
    print(f"\n=== {sid} === BEFORE: status={g.get('status')} sold={g.get('sold_quantity')} title='{(g.get('title') or '')[:70]}'")
    if g.get("status")=="active":
        rp=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30)
        print(f"  pause: {rp.status_code}")
        time.sleep(1)
    rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=30)
    print(f"  close: {rc.status_code} {rc.text[:160] if rc.status_code>=400 else 'OK'}")
    time.sleep(1)
    rd=requests.put(f"{API}/items/{sid}",headers=HJ,json={"deleted":"true"},timeout=30)
    print(f"  delete-flag: {rd.status_code} {'OK' if rd.status_code<400 else rd.text[:160]}")
    time.sleep(1)
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
    print(f"  AFTER: status={g2.get('status')}")
