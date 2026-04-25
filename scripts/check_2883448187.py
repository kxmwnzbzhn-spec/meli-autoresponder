import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2883448187"
d=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
print(f"=== {IID} ===")
print(f"  title: {d.get('title')}")
print(f"  status: {d.get('status')}")
print(f"  sub_status: {d.get('sub_status')}")
print(f"  health: {d.get('health')}")
print(f"  available_quantity: {d.get('available_quantity')}")
print(f"  has_bids: {d.get('has_bids')}")
print(f"  catalog_listing: {d.get('catalog_listing')}")
print(f"  catalog_product_id: {d.get('catalog_product_id')}")
print(f"  date_created: {d.get('date_created')}")
print(f"  last_updated: {d.get('last_updated')}")
print(f"  variations: {len(d.get('variations') or [])}")
for v in (d.get("variations") or []):
    color=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    print(f"    {color} id={v.get('id')} qty={v.get('available_quantity')} sold={v.get('sold_quantity',0)}")
