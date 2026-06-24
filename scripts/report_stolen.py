import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT_AH=os.environ["MELI_REFRESH_TOKEN_AH"]
RT_MAY=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]

# Get Adrián token
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_AH},timeout=20)
AT_AH=r.json()["access_token"]
H_AH={"Authorization":f"Bearer {AT_AH}"}

# Get source item full
src=requests.get(f"{API}/items/MLM3025719815?include_attributes=all",headers=H_AH,timeout=15).json()
print("Source:",src.get("title"),"price:",src.get("price"),"cat:",src.get("category_id"),"listing:",src.get("listing_type_id"))
print("attrs count:",len(src.get("attributes",[])))
print("pics count:",len(src.get("pictures",[])))

# Get description
desc=requests.get(f"{API}/items/MLM3025719815/description",headers=H_AH,timeout=10).json()
desc_text=desc.get("plain_text","")
print("desc bytes:",len(desc_text))

# Switch to Mayrely
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_MAY},timeout=20)
AT_M=r.json()["access_token"]
HJ_M={"Authorization":f"Bearer {AT_M}","Content-Type":"application/json"}

# Build clone payload (tradicional, NO catalog_listing)
attrs=[]
for a in src.get("attributes",[]):
  aid=a.get("id"); v=a.get("value_name")
  if not aid or not v: continue
  # skip auto fields
  if aid in ("ITEM_CONDITION","CATALOG_PRODUCT_ID","UNIVERSAL_PRODUCT_CODE","SELLER_SKU"): continue
  attrs.append({"id":aid,"value_name":v})

payload={
  "title":src.get("title"),
  "category_id":src.get("category_id"),
  "price":src.get("price"),
  "currency_id":"MXN",
  "available_quantity":src.get("available_quantity") or 1,
  "buying_mode":"buy_it_now",
  "listing_type_id":"gold_pro",
  "condition":"new",
  "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in src.get("pictures",[])[:12]],
  "attributes":attrs,
  "sale_terms":src.get("sale_terms",[]),
}
r=requests.post(f"{API}/items",headers=HJ_M,json=payload,timeout=40)
print(f"\nPUBLISH: {r.status_code}")
j={}
try: j=r.json()
except: pass
new_id=j.get("id")
print(f"new_id: {new_id}")
if r.status_code>=400:
  print(r.text[:1500])
else:
  # Add description
  if desc_text:
    dd=requests.post(f"{API}/items/{new_id}/description",headers=HJ_M,json={"plain_text":desc_text},timeout=15)
    print("desc:",dd.status_code)
