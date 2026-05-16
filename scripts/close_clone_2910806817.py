import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

OLD="MLM2910806817"
g=requests.get(f"https://api.mercadolibre.com/items/{OLD}",headers=H).json()
print(f"OLD st={g.get('status')} sold={g.get('sold_quantity')} price=${g.get('price')} title={(g.get('title') or '')[:60]}")
title=g.get("title")
cat=g.get("category_id")
cpid=g.get("catalog_product_id")
price=int(g.get("price",0))
desc=requests.get(f"https://api.mercadolibre.com/items/{OLD}/description",headers=H).json().get("plain_text") or ""

# Build new body (same as old, catalog_listing)
body={
    "title":title,"category_id":cat,"price":price,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":g.get("listing_type_id") or "gold_pro",
    "condition":g.get("condition","new"),
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"90 días"}],
}
if cpid:
    body["catalog_listing"]=True
    body["catalog_product_id"]=cpid
print(f"\nCloning catalog={cpid} price=${price}")
r=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body)
print(f"POST http={r.status_code}")
new_id=None
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"NEW_ID={new_id} status={r.json().get('status')}")
    if desc:
        d=requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=HJ,json={"plain_text":desc})
        if d.status_code>=300:
            d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=HJ,json={"plain_text":desc})
        print(f"DESC http={d.status_code}")
else:
    print(f"ERR: {r.text[:500]}")

# Now close old (only if new was created successfully)
if new_id:
    time.sleep(2)
    r1=requests.put(f"https://api.mercadolibre.com/items/{OLD}",headers=HJ,json={"status":"paused"})
    print(f"\nPAUSE OLD {OLD} http={r1.status_code}")
    time.sleep(1)
    r2=requests.put(f"https://api.mercadolibre.com/items/{OLD}",headers=HJ,json={"status":"closed"})
    print(f"CLOSE OLD {OLD} http={r2.status_code}")
