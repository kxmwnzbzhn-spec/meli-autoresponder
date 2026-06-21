import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

RT_A=os.environ["MELI_REFRESH_TOKEN_AH"]
ra=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_A},timeout=20)
AT_A=ra.json()["access_token"]; HA={"Authorization":f"Bearer {AT_A}"}

RT_M=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
rm=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_M},timeout=20)
AT_M=rm.json()["access_token"]; HM={"Authorization":f"Bearer {AT_M}"}
HJM={**HM,"Content-Type":"application/json"}

# Use the chart 5732536 we created earlier
NEW_GRID="5732536"
print(f"Using NEW_GRID={NEW_GRID}")
fc=requests.get(f"{API}/catalog/charts/{NEW_GRID}",headers=HM,timeout=15).json()
new_size_to_id={}
for r in fc.get("rows",[]):
  for a in r.get("attributes",[]):
    if a.get("id")=="SIZE":
      sz=a.get("values",[{}])[0].get("name")
      new_size_to_id[sz]=r.get("id")
print(f"new sizes: {new_size_to_id}")

PICS=["843389-MLM112420198538_062026","853216-MLM113582132069_062026","692677-MLM113582132089_062026","846114-MLM113581959235_062026","958878-MLM112420024468_062026","644308-MLM112420308530_062026","885995-MLM113582132141_062026","909513-MLM112420024518_062026","835666-MLM112419905686_062026","821832-MLM112420024554_062026"]

SRC="MLM2976325463"
src=requests.get(f"{API}/items/{SRC}",headers=HA,timeout=15).json()
dr=requests.get(f"{API}/items/{SRC}/description",headers=HA,timeout=15)
desc=dr.json().get("plain_text","") if dr.status_code==200 else ""

variations=[]
for v in src.get("variations",[]):
  combo=[]
  for ac in v.get("attribute_combinations",[]) or []:
    e={"id":ac.get("id")}
    if ac.get("value_id"): e["value_id"]=ac.get("value_id")
    if ac.get("value_name"): e["value_name"]=ac.get("value_name")
    combo.append(e)
  v_attrs=[]
  for ac in v.get("attributes",[]) or []:
    e={"id":ac.get("id")}
    if ac.get("value_id"): e["value_id"]=ac.get("value_id")
    if ac.get("value_name"): e["value_name"]=ac.get("value_name")
    v_attrs.append(e)
  size=None
  for ac in (v.get("attributes") or [])+(v.get("attribute_combinations") or []):
    if ac.get("id")=="SIZE": size=ac.get("value_name")
  new_row_id=new_size_to_id.get(size)
  if new_row_id:
    v_attrs.append({"id":"SIZE_GRID_ROW_ID","value_name":str(new_row_id)})
  variations.append({
    "attribute_combinations": combo,
    "attributes": v_attrs,
    "available_quantity": v.get("available_quantity") or 10,
    "price": v.get("price") or src.get("price"),
    "picture_ids": PICS[:3]
  })

keep={"BRAND","GENDER","MAIN_MATERIAL","UNITS_PER_PACK","ITEM_CONDITION","MODEL","LINE","CLOTHING_TYPE","UNDERWEAR_TYPE","PATTERN","DESIGN","MAIN_COLOR","COLOR"}
attrs=[]
for a in src.get("attributes",[]):
  aid=a.get("id")
  if aid in keep and aid!="SIZE":
    e={"id":aid}
    if a.get("value_id"): e["value_id"]=a.get("value_id")
    if a.get("value_name"): e["value_name"]=a.get("value_name")
    attrs.append(e)
attrs.append({"id":"SIZE_GRID_ID","value_name":NEW_GRID})

payload={
  "title": src.get("title"),
  "category_id": src.get("category_id"),
  "price": src.get("price") or 399,
  "currency_id":"MXN","listing_type_id":"gold_special","condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in PICS],
  "attributes": attrs,
  "variations": variations,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc[:5000]}
}

p=requests.post(f"{API}/items",headers=HJM,json=payload,timeout=30)
print(f"\nPOST item: {p.status_code}")
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJM,json={"plain_text":desc[:5000]},timeout=20)
  print(f"\n✅ CLONED to Mayrely: {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
