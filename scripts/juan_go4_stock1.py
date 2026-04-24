import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2883448187"
cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=variations,available_quantity",headers=H).json()
new_vars=[]
for v in (cur.get("variations") or []):
    color=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    print(f"  {color} id={v.get('id')} antes={v.get('available_quantity')}")
    new_vars.append({
        "id":v.get("id"),
        "price":v.get("price"),
        "available_quantity":1,
        "attribute_combinations":v.get("attribute_combinations",[]),
        "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
    })

rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"variations":new_vars},timeout=30)
print(f"\nupdate: {rp.status_code}")
if rp.status_code not in (200,201):
    print(rp.text[:800])
else:
    print("*** OK stock visible = 1 por color ***")
