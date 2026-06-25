import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
def tk(rt):
  return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20).json()["access_token"]
AT_AH=tk(os.environ["MELI_REFRESH_TOKEN_AH"])
AT_MAY=tk(os.environ["MELI_REFRESH_TOKEN_MAYRELY"])
H_AH={"Authorization":f"Bearer {AT_AH}"}
HJ_M={"Authorization":f"Bearer {AT_MAY}","Content-Type":"application/json"}

# Manual titles ≤60 chars
TITLES={
  "MLM3025478283":"Bocina Beats Pill Bluetooth Negro Mate Reacondicionada",
  "MLM3018014885":"Marshall Emberton Bluetooth Reacondicionada Negro",
}
for src_id in ["MLM3025478283","MLM3018014885"]:
  src=requests.get(f"{API}/items/{src_id}?include_attributes=all",headers=H_AH,timeout=15).json()
  desc=requests.get(f"{API}/items/{src_id}/description",headers=H_AH,timeout=10).json()
  desc_text=desc.get("plain_text","") or ""
  attrs=[]
  has_gtin=False
  for a in src.get("attributes",[]):
    aid=a.get("id"); v=a.get("value_name")
    if not aid or not v: continue
    if aid in ("ITEM_CONDITION","CATALOG_PRODUCT_ID","UNIVERSAL_PRODUCT_CODE","SELLER_SKU","UPC","UPC_ID","HAZMAT_TRANSPORTABILITY"): continue
    if aid=="GTIN": has_gtin=True
    attrs.append({"id":aid,"value_name":v})
  if not has_gtin:
    attrs.append({"id":"GTIN","value_name":"No aplica"})
  payload={
    "title":TITLES[src_id],
    "category_id":src.get("category_id"),
    "price":src.get("price"),
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in src.get("pictures",[])[:12]],
    "attributes":attrs,
    "sale_terms":src.get("sale_terms",[]),
  }
  r=requests.post(f"{API}/items",headers=HJ_M,json=payload,timeout=40)
  j=r.json() if r.status_code<500 else {}
  new_id=j.get("id")
  print(f"{src_id} -> {r.status_code} {new_id} ${src.get('price')} title='{TITLES[src_id]}'")
  if r.status_code>=400:
    print(f"  ERR: {r.text[:600]}")
  else:
    if desc_text:
      dd=requests.post(f"{API}/items/{new_id}/description",headers=HJ_M,json={"plain_text":desc_text},timeout=15)
      print(f"  desc: {dd.status_code}")
