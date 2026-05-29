import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM2967318191"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
print(f"BEFORE: status={g.get('status')} sub={g.get('sub_status')} price={g.get('price')} qty={g.get('available_quantity')} cpid={g.get('catalog_product_id')} title='{(g.get('title') or '')[:65]}'")
qty=g.get('available_quantity') or 0
body={"status":"active"}
if qty<1: body["available_quantity"]=1
r=requests.put(f"{API}/items/{sid}",headers=HJ,json=body,timeout=30)
print(f"PUT {body}: {r.status_code} {r.text[:300] if r.status_code>=400 else 'OK'}")
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=20).json()
print(f"AFTER: status={g2.get('status')} sub={g2.get('sub_status')} qty={g2.get('available_quantity')}")
