import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LUPITA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5638926762"
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"BEFORE: status={g.get('status')} qty={g.get('available_quantity')} price=${g.get('price')} sub={g.get('sub_status')} health={g.get('health')}",flush=True)

# Try to reactivate step by step
if g.get("status")=="closed":
    # closed is normally irreversible but let's see
    r1=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"active","available_quantity":1},timeout=15).json()
    print(f"reopen: {json.dumps(r1)[:400]}",flush=True)
elif g.get("status")=="paused":
    r1=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"active","available_quantity":1},timeout=15).json()
    print(f"activate: status={r1.get('status')} qty={r1.get('available_quantity')} err={r1.get('error','')}",flush=True)
elif g.get("status")=="under_review":
    print("under_review — MELI reviewing, cannot force",flush=True)
elif g.get("status")=="active" and g.get("available_quantity",0)==0:
    r1=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"available_quantity":1},timeout=15).json()
    print(f"restock: qty={r1.get('available_quantity')} err={r1.get('error','')}",flush=True)
else:
    print(f"status={g.get('status')} — no acción",flush=True)

# Also check sub_status for reason
g2=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"AFTER: status={g2.get('status')} qty={g2.get('available_quantity')} sub={g2.get('sub_status')}",flush=True)
