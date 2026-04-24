import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

CID="5502336104"
# Detalle
c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}",headers=H).json()
print("=== CLAIM ===")
print(json.dumps(c,ensure_ascii=False,indent=2)[:2500])

# Orden
ORDER=c.get("resource_id")
o=requests.get(f"https://api.mercadolibre.com/orders/{ORDER}",headers=H).json()
print(f"\n=== ORDER {ORDER} ===")
buyer=o.get("buyer") or {}
print(f"buyer: {buyer.get('nickname')} ({buyer.get('id')})")
for it in (o.get("order_items") or []):
    i=it.get("item") or {}
    print(f"item: {i.get('id')} | '{i.get('title','')}' | qty={it.get('quantity')}")
    ITEM_ID=i.get("id")

# Descripcion del item
if ITEM_ID:
    d=requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}/description",headers=H).json()
    print(f"\n=== DESC ITEM ({len(d.get('plain_text',''))} chars) ===")
    print(d.get("plain_text","")[:2000])

# Mensajes del claim
m=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages",headers=H).json()
print(f"\n=== MENSAJES ({len(m) if isinstance(m,list) else 0}) ===")
if isinstance(m,list):
    for msg in m:
        print(f"  {msg.get('sender_role')} @ {msg.get('date_created','')[:19]}: {str(msg.get('message'))[:250]}")
