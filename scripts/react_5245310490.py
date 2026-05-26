import os, json, requests, sys
sys.path.insert(0, "scripts")
import meli_token
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM5245310490"
g=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"BEFORE: status={g.get('status')} price={g.get('price')} qty={g.get('available_quantity')} variations={len(g.get('variations',[]))}")
# Set price first
r1=requests.put(f"{API}/items/{sid}",headers=HJ,json={"price":499},timeout=30)
print(f"PRICE: {r1.status_code} {r1.text[:200]}")
# Set quantity if needed
if g.get("variations"):
    # has variations, set qty per variation if 0
    vars_payload=[]
    for v in g["variations"]:
        cur_qty=v.get("available_quantity",0)
        vars_payload.append({"id":v["id"],"available_quantity":max(cur_qty,1)})
    r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"variations":vars_payload},timeout=30)
    print(f"VAR_QTY: {r2.status_code} {r2.text[:200]}")
else:
    if (g.get("available_quantity") or 0)<1:
        r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"available_quantity":1},timeout=30)
        print(f"QTY: {r2.status_code} {r2.text[:200]}")
# Activate
r3=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active"},timeout=30)
print(f"ACTIVATE: {r3.status_code} {r3.text[:200]}")
# Verify
g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=30).json()
print(f"FINAL: status={g2.get('status')} price={g2.get('price')} qty={g2.get('available_quantity')}")
