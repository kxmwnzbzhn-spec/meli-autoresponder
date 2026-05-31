import os, requests, time
API="https://api.mercadolibre.com"
def t(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=15).json()

# Pause Yiriam active
print("=== Yiriam pause active ===")
ty=t(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]); TY=ty["access_token"]; print(f"NEW_RT_YC_NEW={ty.get('refresh_token')}")
HY={"Authorization":f"Bearer {TY}"}; HJY={**HY,"Content-Type":"application/json"}
UIDY=requests.get(f"{API}/users/me",headers=HY,timeout=10).json()["id"]
r=requests.get(f"{API}/users/{UIDY}/items/search?status=active&limit=50",headers=HY,timeout=15).json()
for sid in (r.get("results") or [])[:10]:
    pr=requests.put(f"{API}/items/{sid}",headers=HJY,json={"status":"paused"},timeout=20)
    print(f"  pause {sid}: {pr.status_code}")
    time.sleep(0.3)

# Mass revive OOS in non-FBM accounts: Claribel, Juan, Yiriam, Wilbert
for acc_sec,nick in [("MELI_REFRESH_TOKEN_CLARIBEL","Claribel"),("MELI_REFRESH_TOKEN_JUAN","Juan"),("MELI_REFRESH_TOKEN_YC_NEW","Yiriam"),("MELI_REFRESH_TOKEN_WILBERT","Wilbert")]:
    print(f"\n=== {nick} mass-revive OOS ===")
    tt=t(os.environ[acc_sec]); TT=tt["access_token"]
    HX={"Authorization":f"Bearer {TT}"}; HJX={**HX,"Content-Type":"application/json"}
    UID=requests.get(f"{API}/users/me",headers=HX,timeout=10).json()["id"]
    paused_ids=[]
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status=paused&limit=50&offset={off}",headers=HX,timeout=15).json()
        res=r.get("results") or []
        paused_ids.extend(res)
        if len(res)<50 or off>2000: break
        off+=50
    revived=0; skipped_fbm=0
    for i in range(0,len(paused_ids),20):
        batch=",".join(paused_ids[i:i+20])
        mg=requests.get(f"{API}/items",headers=HX,params={"ids":batch,"attributes":"id,sub_status,inventory_id"},timeout=15).json()
        for x in mg:
            if x.get("code")!=200: continue
            b=x["body"]
            if "out_of_stock" not in (b.get("sub_status") or []): continue
            if b.get("inventory_id"): skipped_fbm+=1; continue
            r2=requests.put(f"{API}/items/{b['id']}",headers=HJX,json={"status":"active","available_quantity":1},timeout=15)
            if r2.status_code in (200,201): revived+=1
        time.sleep(0.1)
    print(f"  scanned_paused={len(paused_ids)} revived={revived} skipped_fbm={skipped_fbm}")
