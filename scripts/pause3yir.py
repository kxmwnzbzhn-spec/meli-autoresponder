import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_YC_NEW={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
IDS=["MLM5291785036","MLM2950790163","MLM2909183147"]
for sid in IDS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
    print(f"\n{sid} BEFORE: status={g.get('status')} sold={g.get('sold_quantity')} price={g.get('price')} title='{(g.get('title') or '')[:65]}'")
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30)
    print(f"  pause: {r.status_code} {r.text[:160] if r.status_code>=400 else 'OK'}")
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
    print(f"  AFTER: status={g2.get('status')}")
    time.sleep(0.4)
