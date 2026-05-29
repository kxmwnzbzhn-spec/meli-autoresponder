import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
# list paused
paused=[]
off=0
while True:
    r=requests.get(f"{API}/users/{UID}/items/search?status=paused&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    paused.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
print(f"\nClaribel paused: {len(paused)}")
oos=[]; other=[]
for i in range(0,len(paused),20):
    batch=",".join(paused[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,sub_status,price,sold_quantity"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        if "out_of_stock" in (b.get("sub_status") or []):
            oos.append(b)
        else:
            other.append(b)
print(f"  out_of_stock (debe reactivar bot): {len(oos)}")
for b in oos:
    print(f"    {b['id']} ${b.get('price')} sold={b.get('sold_quantity')} | {(b.get('title') or '')[:60]}")
print(f"  otros sub_status (NO tocar): {len(other)}")
for b in other:
    print(f"    {b['id']} ${b.get('price')} sub={b.get('sub_status')} | {(b.get('title') or '')[:60]}")
