import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
YIR=["MLM5353056250","MLM2935286537","MLM2935286557","MLM2935445653","MLM5353154356","MLM2935286605","MLM2935274091","MLM2935286651","MLM5353056406","MLM2935286681","MLM2935286703","MLM2935298361"]
for iid in YIR:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    st=g.get("status"); sub=g.get("sub_status",[]); qty=g.get("available_quantity",0)
    title=(g.get("title") or "")[:35]
    print(f"\n{iid} '{title}' st={st} sub={sub} qty={qty}")
    if st=="closed":
        # Try relist
        r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=HJ,json={"quantity":1,"listing_type_id":g.get("listing_type_id") or "gold_pro"})
        print(f"  RELIST http={r.status_code} {r.text[:200]}")
        if r.status_code<300: print(f"  NEW_ID={r.json().get('id')}")
        continue
    if st=="paused":
        # Multi-step: clear out_of_stock then activate
        # 1) set qty 1
        r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1})
        print(f"  SET qty=1 http={r1.status_code} {r1.text[:150] if r1.status_code>=300 else ''}")
        time.sleep(0.5)
        # 2) set active
        r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"})
        print(f"  ACTIVATE http={r2.status_code} {r2.text[:150] if r2.status_code>=300 else ''}")
        time.sleep(0.5)
        # verify
        g2=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,available_quantity,sub_status",headers=H).json()
        print(f"  AFTER st={g2.get('status')} sub={g2.get('sub_status')} qty={g2.get('available_quantity')}")
