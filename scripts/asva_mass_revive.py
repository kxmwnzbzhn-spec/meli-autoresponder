"""Revive masivo: pagina TODOS los paused de ASVA, filtra OOS, reactiva con qty=1."""
import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]

# Page through ALL paused
all_paused=[]
off=0
while True:
    r=requests.get(f"{API}/users/{UID}/items/search?status=paused&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    all_paused.extend(res)
    if len(res)<50 or off>2000: break
    off+=50
print(f"Paginated paused: {len(all_paused)}")

# Filter OOS via multiget
oos=[]
for i in range(0,len(all_paused),20):
    batch=",".join(all_paused[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,sub_status"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        if "out_of_stock" in (b.get("sub_status") or []):
            oos.append(b["id"])
print(f"OOS to revive: {len(oos)}")

ok=err=0
for i,sid in enumerate(oos,1):
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=15)
    if r.status_code in (200,201): ok+=1
    else:
        err+=1
        print(f"  [{i}/{len(oos)}] {sid} ERR {r.status_code} {r.text[:120]}")
    if i%25==0: print(f"  progress: {i}/{len(oos)} ok={ok} err={err}")
    time.sleep(0.2)
print(f"\n=== DONE === total={len(oos)} ok={ok} err={err}")
