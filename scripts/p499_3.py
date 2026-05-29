import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
IDS=["MLM2967317613","MLM2967292003","MLM2967317601"]
for sid in IDS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"\n{sid} BEFORE: status={g.get('status')} price={g.get('price')} qty={g.get('available_quantity')} title='{(g.get('title') or '')[:60]}'")
    body={"price":499}
    if g.get("status")=="paused":
        body["status"]="active"
        body["available_quantity"]=1
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json=body,timeout=20)
    print(f"  PUT {body}: {r.status_code} {r.text[:150] if r.status_code>=400 else 'OK'}")
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"  AFTER: status={g2.get('status')} price={g2.get('price')}")
    time.sleep(0.3)
