import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM2950790163"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"BEFORE: status={g.get('status')} sold={g.get('sold_quantity')} price={g.get('price')} title='{(g.get('title') or '')[:80]}'")
r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=30)
print(f"pause: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"AFTER: status={g2.get('status')}")
