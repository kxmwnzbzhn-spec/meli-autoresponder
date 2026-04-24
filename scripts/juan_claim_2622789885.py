import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Juan: {me.get('nickname')} {me.get('id')}")

ID="2000012622789885"
# Buscar como orden
print(f"\n=== ORDER {ID} ===")
o=requests.get(f"https://api.mercadolibre.com/orders/{ID}",headers=H,timeout=15)
print(f"  status: {o.status_code}")
ORDER_DATA=None
if o.status_code==200:
    ORDER_DATA=o.json()
    print(f"  order_id={ORDER_DATA.get('id')} pack_id={ORDER_DATA.get('pack_id')} status={ORDER_DATA.get('status')} status_detail={ORDER_DATA.get('status_detail')}")
    print(f"  buyer: {(ORDER_DATA.get('buyer') or {}).get('nickname')} ({(ORDER_DATA.get('buyer') or {}).get('id')})")
    for it in (ORDER_DATA.get("order_items") or []):
        i=it.get("item") or {}
        print(f"  item: {i.get('id')} '{i.get('title','')}' qty={it.get('quantity')}")
    # Cancelacion detail
    for k in ("cancel_detail","order_cancellation","cancel_reason"):
        if ORDER_DATA.get(k): print(f"  {k}: {ORDER_DATA.get(k)}")

# Buscar claim por esta orden o pack
print(f"\n=== SEARCH CLAIMS ===")
for rtype in ["order","pack"]:
    s=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource={rtype}&resource_id={ID}",headers=H,timeout=15)
    print(f"  {rtype}: {s.status_code}")
    if s.status_code==200:
        for c in (s.json().get("data") or []):
            print(f"    CLAIM id={c.get('id')} reason={c.get('reason_id')} stage={c.get('stage')} status={c.get('status')}")

# Listar todos open/closed recientes
print("\n=== TODOS CLAIMS (todos estados) ===")
for q in ["?status=opened","?status=closed&sort=date_created,desc&limit=10"]:
    al=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search{q}",headers=H,timeout=15)
    if al.status_code==200:
        print(f"  {q}:")
        for c in (al.json().get("data") or [])[:10]:
            print(f"    id={c.get('id')} res={c.get('resource_id')} reason={c.get('reason_id')} stage={c.get('stage')} status={c.get('status')}")

# Si hay pack_id, obtener detalles
if ORDER_DATA and ORDER_DATA.get("pack_id"):
    pid=ORDER_DATA.get("pack_id")
    print(f"\n=== PACK {pid} ===")
    p=requests.get(f"https://api.mercadolibre.com/packs/{pid}",headers=H,timeout=15)
    if p.status_code==200: print(json.dumps(p.json(),ensure_ascii=False)[:1000])
