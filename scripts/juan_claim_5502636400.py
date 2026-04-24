import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

CID="5502636400"
c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}",headers=H).json()
print("=== CLAIM ===")
print(json.dumps(c,ensure_ascii=False,indent=2)[:2500])

ORDER=c.get("resource_id")
o=requests.get(f"https://api.mercadolibre.com/orders/{ORDER}",headers=H).json()
print(f"\n=== ORDER {ORDER} ===")
buyer=o.get("buyer") or {}
print(f"buyer: {buyer.get('nickname')} ({buyer.get('id')})")
for it in (o.get("order_items") or []):
    i=it.get("item") or {}
    print(f"item: {i.get('id')} '{i.get('title','')}' qty={it.get('quantity')}")
    ITEM_ID=i.get("id")

d=requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}?include_attributes=all",headers=H).json()
print(f"\ncondition: {d.get('condition')}")
print(f"brand: {next((a.get('value_name') for a in (d.get('attributes') or []) if a.get('id')=='BRAND'),'')}")
desc=requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}/description",headers=H).json().get("plain_text","")
print(f"\n=== DESC ({len(desc)}c) ===\n{desc[:2500]}")

# Mensajes
m=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CID}/messages",headers=H).json()
print(f"\n=== MENSAJES ({len(m) if isinstance(m,list) else 0}) ===")
if isinstance(m,list):
    for msg in m:
        print(f"  {msg.get('sender_role')} @ {msg.get('date_created','')[:19]}: {str(msg.get('message'))[:400]}")
