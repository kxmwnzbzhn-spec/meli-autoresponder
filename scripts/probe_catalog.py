import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
# Explorar producto catálogo de referencia (Go 4 que sí funciona con variations)
for cid in ["MLM64277114","MLM47809508","MLM36723320","MLM29772333","MLM61316998"]:
    d=requests.get(f"https://api.mercadolibre.com/products/{cid}",headers=H).json()
    print(f"=== {cid} ===")
    print(f"  name: {d.get('name','')[:80]}")
    print(f"  family_id: {d.get('family_id')}")
    print(f"  parent_id: {d.get('parent_id')}")
    print(f"  children_ids: {(d.get('children_ids') or [])[:5]}")
    print(f"  main_features_type: {d.get('main_features_type')}")
    # mira attrs de COLOR
    for a in (d.get("attributes") or []):
        if a.get("id")=="COLOR":
            print(f"  COLOR: {a.get('value_name')}")
