import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM5245310490"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"BEFORE: status={g.get('status')} price={g.get('price')} qty={g.get('available_quantity')} variations={len(g.get('variations',[]))}")
r1=requests.put(f"{API}/items/{sid}",headers=HJ,json={"price":499},timeout=30)
print(f"PRICE: {r1.status_code} {r1.text[:300]}")
if g.get("variations"):
    vars_payload=[]
    for v in g["variations"]:
        cur_qty=v.get("available_quantity",0)
        vars_payload.append({"id":v["id"],"available_quantity":max(cur_qty,1)})
    r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"variations":vars_payload},timeout=30)
    print(f"VAR_QTY: {r2.status_code} {r2.text[:300]}")
else:
    if (g.get("available_quantity") or 0)<1:
        r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"available_quantity":1},timeout=30)
        print(f"QTY: {r2.status_code} {r2.text[:300]}")
r3=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active"},timeout=30)
print(f"ACTIVATE: {r3.status_code} {r3.text[:300]}")
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"FINAL: status={g2.get('status')} price={g2.get('price')} qty={g2.get('available_quantity')}")
