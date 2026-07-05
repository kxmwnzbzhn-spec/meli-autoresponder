import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=[("MLM3066033037","L"),("MLM3066095021","M"),("MLM5607789818","S")]
TARGET_QTY=3

for iid, size in ITEMS:
    print(f"\n=== {iid} (Talla {size}) ===",flush=True)
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    print(f"  BEFORE: status={g.get('status')} qty={g.get('available_quantity')} sub={g.get('sub_status')}",flush=True)
    
    if g.get("variations"):
        # Item has variations - restock each variation
        vars_new=[]
        for v in g["variations"]:
            vars_new.append({"id":v["id"], "available_quantity":TARGET_QTY})
        payload={"status":"active", "variations":vars_new}
        print(f"  variations: {len(vars_new)} -> qty={TARGET_QTY} each",flush=True)
    else:
        payload={"status":"active", "available_quantity":TARGET_QTY}
    
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=payload,timeout=15).json()
    print(f"  AFTER: status={r.get('status')} qty={r.get('available_quantity')} err={r.get('error','')}",flush=True)
    if r.get("error"):
        print(f"  err detail: {json.dumps(r)[:400]}",flush=True)
