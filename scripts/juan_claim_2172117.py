import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

ID="2000012592172117"
# Buscar como orden
o=requests.get(f"https://api.mercadolibre.com/orders/{ID}",headers=H,timeout=15)
print(f"=== ORDER {ID}: {o.status_code} ===")
ORDER=None
if o.status_code==200:
    od=o.json()
    ORDER=od
    print(f"  order_id={od.get('id')} pack={od.get('pack_id')} status={od.get('status')} status_detail={od.get('status_detail')}")
    buyer=od.get("buyer") or {}
    print(f"  buyer: {buyer.get('nickname')} ({buyer.get('id')})")
    for it in (od.get("order_items") or []):
        i=it.get("item") or {}
        print(f"  item: {i.get('id')} '{i.get('title','')}' qty={it.get('quantity')} price=${it.get('unit_price')}")

# Buscar claims abiertos
print("\n=== CLAIMS ABIERTOS ===")
s=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened",headers=H,timeout=15).json()
target_claim=None
for c in (s.get("data") or []):
    print(f"  id={c.get('id')} res={c.get('resource_id')} reason={c.get('reason_id')} stage={c.get('stage')}")
    if str(c.get("resource_id"))==ID or (ORDER and str(c.get("resource_id"))==str(ORDER.get("pack_id"))):
        target_claim=c

# Buscar por resource tambien
for rtype in ["order","pack"]:
    s=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource={rtype}&resource_id={ID}",headers=H,timeout=15).json()
    for c in (s.get("data") or []):
        print(f"  [{rtype}] CLAIM id={c.get('id')} reason={c.get('reason_id')} stage={c.get('stage')}")
        target_claim=c

if target_claim:
    cid=target_claim.get("id")
    print(f"\n=== DETALLE CLAIM {cid} ===")
    d=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}",headers=H).json()
    print(json.dumps(d,ensure_ascii=False,indent=2)[:2500])
    # Mensajes
    m=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}/messages",headers=H).json()
    print(f"\n=== MENSAJES ({len(m) if isinstance(m,list) else 0}) ===")
    if isinstance(m,list):
        for msg in m:
            print(f"  {msg.get('sender_role')} @ {msg.get('date_created','')[:19]}: {str(msg.get('message'))[:300]}")
    # Item description
    if ORDER:
        item_id=(ORDER.get("order_items") or [{}])[0].get("item",{}).get("id")
        if item_id:
            it=requests.get(f"https://api.mercadolibre.com/items/{item_id}?attributes=id,title,condition,attributes",headers=H).json()
            print(f"\n=== ITEM {item_id} ===")
            print(f"  title: {it.get('title')}")
            print(f"  condition: {it.get('condition')}")
            brand=next((a.get('value_name') for a in (it.get('attributes') or []) if a.get('id')=='BRAND'),"")
            print(f"  BRAND: {brand}")
            desc=requests.get(f"https://api.mercadolibre.com/items/{item_id}/description",headers=H).json().get("plain_text","")
            print(f"  desc (300c): {desc[:300]}")
