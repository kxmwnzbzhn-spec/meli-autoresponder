import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
d=requests.get("https://api.mercadolibre.com/items/MLM2883448187",headers=H).json()
for k in ("id","title","family_name","user_product_id","catalog_product_id","catalog_listing","domain_id","category_id","status"):
    print(f"{k}: {d.get(k)}")
print("variations:",len(d.get("variations") or []))
for v in (d.get("variations") or [])[:2]:
    print(" ",v.get("id"),"upid=",v.get("user_product_id"),"attrs=",v.get("attribute_combinations"))
