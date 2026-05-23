import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json(); uid=me.get("id")
print(f"Wilbert uid={uid}")

for pass_n in (1,2):
    ids=[]; off=0
    while True:
        r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []; ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50
    print(f"\n=== PASS {pass_n}: active={len(ids)} ===")
    if not ids:
        print("Nada que pausar."); break
    ok=err=0
    for iid in ids:
        try:
            r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
            if r.status_code<300: ok+=1
            else: err+=1
            time.sleep(0.2)
        except: err+=1
    print(f"  ok={ok} err={err}")
    time.sleep(3)

time.sleep(2)
r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=1",headers=H,timeout=15).json()
print(f"\nFINAL active Wilbert: {r.get('paging',{}).get('total',0)}")
