import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]; RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","x-format-new":"true"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json(); uid=me["id"]
# Get one paid order with shipment
o=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.status=paid&limit=3",headers=H,timeout=20).json()
results=o.get("results",[])
if not results:
    print("no orders"); exit()
for ord in results[:2]:
    sid=(ord.get("shipping",{}) or {}).get("id")
    oid=ord.get("id")
    print(f"\n=== ORDER {oid}  SHIPMENT {sid} ===")
    print(f"order.shipping: {json.dumps(ord.get('shipping',{}), ensure_ascii=False)[:300]}")
    
    for ep in [f"/shipments/{sid}", f"/shipments/{sid}/costs", f"/shipments/{sid}/lead_time"]:
        if not sid: continue
        rr=requests.get(f"https://api.mercadolibre.com{ep}",headers=H,timeout=15)
        print(f"\n{ep} → {rr.status_code}")
        try:
            j=rr.json()
            print(json.dumps(j,ensure_ascii=False)[:600])
        except: print(rr.text[:300])
    # Order detail
    rr=requests.get(f"https://api.mercadolibre.com/orders/{oid}",headers=H,timeout=15)
    print(f"\n/orders/{oid} (with x-format-new) → {rr.status_code}")
    try:
        j=rr.json()
        # print only relevant fields
        for k in ("payments","shipping","mediations","fee_details","total_amount","paid_amount","status","status_detail"):
            if k in j: print(f"  {k}: {json.dumps(j[k],ensure_ascii=False)[:400]}")
    except: pass
