import os,json,requests
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()["access_token"]
TY=tok(RT_Y); TW=tok(RT_W)
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}
HW={"Authorization":f"Bearer {TW}","Content-Type":"application/json"}

iid="MLM2911238257"
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=HW).json()
pics=[(p.get("source") or p.get("secure_url") or p.get("url")) for p in (g.get("pictures") or [])][:8]
target=max(int(g.get("price",699))-1,400)

# Catalog listing body — include title + category_id even though catalog
body={
  "title":g["title"],
  "category_id":g["category_id"],
  "catalog_listing":True,
  "catalog_product_id":g["catalog_product_id"],
  "price":target,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "listing_type_id":g.get("listing_type_id") or "gold_pro",
  "condition":"new",
  "pictures":[{"source":p} for p in pics],
  "sale_terms":[s for s in (g.get("sale_terms") or []) if s.get("id") in ("WARRANTY_TYPE","WARRANTY_TIME")]
}
print("SONY title=",g["title"][:60],"cpid=",g["catalog_product_id"],"target=",target)
r=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body)
print("CLONE http=",r.status_code,r.text[:600])
if r.status_code>=300:
  # try simpler
  body2=dict(body); body2.pop("pictures",None); body2.pop("sale_terms",None)
  r2=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body2)
  print("RETRY_NOPICS http=",r2.status_code,r2.text[:600])
  if r2.status_code<300:
    new_id=r2.json().get("id")
    print("NEW_ID:",new_id)
  else:
    # last try: drop catalog_listing flag (publish as traditional)
    body3=dict(body); body3.pop("catalog_listing",None); body3.pop("catalog_product_id",None)
    body3["attributes"]=[{"id":"BRAND","value_name":"Sony"},{"id":"MODEL","value_name":"SRS-XB100"}]
    r3=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body3)
    print("RETRY_TRAD http=",r3.status_code,r3.text[:600])
else:
  print("NEW_ID:",r.json().get("id"))
