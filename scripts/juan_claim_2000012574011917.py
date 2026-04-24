import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"Juan: {me.get('nickname')} {USER_ID}")

ID="2000012574011917"

# Es pack_id / order_id / claim_id?
# Probar como order
print(f"\n=== GET order {ID} ===")
o=requests.get(f"https://api.mercadolibre.com/orders/{ID}",headers=H,timeout=15)
print(f"status: {o.status_code}")
if o.status_code==200:
    od=o.json()
    print(f"  order_id={od.get('id')} pack_id={od.get('pack_id')} status={od.get('status')}")
    buyer=od.get("buyer") or {}
    print(f"  buyer: {buyer.get('nickname')} ({buyer.get('id')})")
    for it in (od.get("order_items") or []):
        i=it.get("item") or {}
        print(f"  item: {i.get('id')} | '{i.get('title','')[:60]}' | qty={it.get('quantity')}")

# Buscar claim por pack/order id
print(f"\n=== SEARCH claims resource_id={ID} ===")
for rtype in ["order","pack"]:
    s=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource={rtype}&resource_id={ID}",headers=H,timeout=15)
    print(f"  resource={rtype}: {s.status_code}")
    if s.status_code==200:
        d=s.json()
        for c in (d.get("data") or []):
            print(f"    CLAIM id={c.get('id')} reason={c.get('reason_id')} stage={c.get('stage')} status={c.get('status')}")

# Listar TODOS los claims abiertos de Juan
print("\n=== ALL OPENED CLAIMS JUAN ===")
al=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened",headers=H,timeout=15)
if al.status_code==200:
    for c in (al.json().get("data") or []):
        print(f"  id={c.get('id')} resource_id={c.get('resource_id')} reason={c.get('reason_id')} stage={c.get('stage')}")
