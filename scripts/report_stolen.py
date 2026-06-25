import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

def tk(rt):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  return r.json()["access_token"]

AT_AH=tk(os.environ["MELI_REFRESH_TOKEN_AH"])
AT_MAY=tk(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])
H_AH={"Authorization":f"Bearer {AT_AH}"}
HJ_M={"Authorization":f"Bearer {AT_MAY}","Content-Type":"application/json"}

SOURCES=["MLM5525982716","MLM3034001565","MLM3025478283","MLM3018014885","MLM3034025531"]
results={}
for src_id in SOURCES:
  src=requests.get(f"{API}/items/{src_id}?include_attributes=all",headers=H_AH,timeout=15).json()
  print(f"\n=== {src_id}: {src.get('title')[:60]} ===")
  print(f"  status={src.get('status')} cat={src.get('category_id')} price={src.get('price')} qty={src.get('available_quantity')}")
  print(f"  catalog_listing={src.get('catalog_listing')} cpid={src.get('catalog_product_id')} cond={src.get('condition')} listing={src.get('listing_type_id')}")
  desc=requests.get(f"{API}/items/{src_id}/description",headers=H_AH,timeout=10).json()
  desc_text=desc.get("plain_text","") or ""
  print(f"  desc bytes: {len(desc_text)}, pics: {len(src.get('pictures',[]))}, attrs: {len(src.get('attributes',[]))}")

  attrs=[]
  for a in src.get("attributes",[]):
    aid=a.get("id"); v=a.get("value_name")
    if not aid or not v: continue
    if aid in ("ITEM_CONDITION","CATALOG_PRODUCT_ID","UNIVERSAL_PRODUCT_CODE","SELLER_SKU","UPC","UPC_ID"): continue
    attrs.append({"id":aid,"value_name":v})

  payload={
    "title":src.get("title"),
    "category_id":src.get("category_id"),
    "price":src.get("price"),
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":src.get("listing_type_id") or "gold_pro",
    "condition":src.get("condition") or "new",
    "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in src.get("pictures",[])[:12]],
    "attributes":attrs,
    "sale_terms":src.get("sale_terms",[]),
  }
  r=requests.post(f"{API}/items",headers=HJ_M,json=payload,timeout=40)
  j={}
  try: j=r.json()
  except: pass
  new_id=j.get("id")
  print(f"  CLONE: {r.status_code} -> {new_id}")
  if r.status_code>=400:
    print(f"  ERR: {r.text[:500]}")
  else:
    if desc_text:
      dd=requests.post(f"{API}/items/{new_id}/description",headers=HJ_M,json={"plain_text":desc_text},timeout=15)
      print(f"  desc: {dd.status_code}")
  results[src_id]={"item":new_id,"status":r.status_code,"price":src.get("price"),"cond":src.get("condition"),"title":src.get("title","")[:50]}

print("\n=== RESULTS ===")
print(json.dumps(results,indent=2,default=str))
