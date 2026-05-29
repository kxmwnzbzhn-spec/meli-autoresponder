import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

# List paused only
ids=[]
off=0
while True:
    r=requests.get(f"{API}/users/{UID}/items/search?status=paused&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    ids.extend(res)
    if len(res)<50 or off>1500: break
    off+=50
print(f"\nASVA paused total: {len(ids)}")

oos=[]; other=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,sub_status,price,sold_quantity,available_quantity"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        ss=b.get("sub_status") or []
        rec=(b["id"],b.get("title","")[:55],ss,b.get("price"),b.get("available_quantity"),b.get("sold_quantity"))
        if "out_of_stock" in ss: oos.append(rec)
        else: other.append(rec)

print(f"\nout_of_stock (deberían reactivarse): {len(oos)}")
for r in oos:
    print(f"  {r[0]} ${r[3]} qty={r[4]} sold={r[5]} | {r[1]}")

print(f"\notros sub_status: {len(other)}")
for r in other:
    print(f"  {r[0]} ${r[3]} sub={r[2]} sold={r[5]} | {r[1]}")
