import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
MIN_FLOOR=200

for iid in ["MLM5364336572","MLM5364336602"]:
    print(f"\n=== {iid} ===")
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price"); cpid=g.get("catalog_product_id"); st=g.get("status")
    print(f"  status={st} cur=${cur} cpid={cpid}")
    if st!="active":
        # activar
        if g.get("available_quantity",0)==0:
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=10); time.sleep(0.3)
        ra=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"  REACT http={ra.status_code}")
    # PTW
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {p.get('status')} ptw={p.get('price_to_win')}")
    # low_ext
    pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
    ext=[]
    for r2 in (pr.get("results") or []):
        rid=r2.get("item_id") or r2.get("id"); rp=r2.get("price")
        rst=(r2.get("status") or "active").lower(); rq=r2.get("available_quantity",1)
        if rid and rid!=iid and rp and rst=="active" and rq>0: ext.append((rid,rp))
    ext.sort(key=lambda x:x[1])
    print(f"  Competidores top3: {ext[:3]}")
    if ext:
        low_ext=ext[0][1]
        if cur >= low_ext:
            target=max(int(low_ext)-5, MIN_FLOOR)
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            print(f"  DROP ${cur}→${target} (low_ext=${low_ext}) http={r.status_code}")
        else:
            print(f"  Ya #1 (cur ${cur} < low_ext ${low_ext}), hold")
    else:
        print(f"  Sin competidores, #1 solo")
    time.sleep(0.5)
    # verificar
    p2=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW post: {p2.get('status')}")
