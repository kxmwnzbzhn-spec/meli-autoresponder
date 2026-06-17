import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# =========================================
# A) CLONAR MLM5519420804 (JBL Go4 usada) con stock 200
# =========================================
print("=== A) CLONE JBL Go4 usada w/ stock 200 ===")
SRC="MLM5519420804"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
pic_ids=[p.get("id") for p in src.get("pictures",[]) if p.get("id")]
sd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=15).json()
desc_go=sd.get("plain_text","")
print(f"src pics: {len(pic_ids)}  desc: {len(desc_go)}")
src_attrs=src.get("attributes",[])
keep=["BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","GTIN"]
attrs_go=[]
for a in src_attrs:
  if a.get("id") in keep and a.get("value_name"):
    attrs_go.append({"id":a["id"],"value_name":a["value_name"]})
if not any(a["id"]=="GTIN" for a in attrs_go):
  attrs_go.append({"id":"GTIN","value_name":"6925281982989"})  # JBL Go 4 EAN

payload_go={
  "title": src.get("title"),
  "category_id": src.get("category_id"),
  "price": src.get("price"),
  "currency_id":"MXN",
  "available_quantity":200,
  "listing_type_id":"gold_special",
  "condition":"used",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs_go,
  "shipping":{"mode":"me2","free_shipping":True,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc_go}
}
pg=requests.post(f"{API}/items",headers=HJ,json=payload_go,timeout=30)
print("Go4 clone POST:",pg.status_code)
print(pg.text[:1500])
go_new=None
if pg.status_code==201:
  d=pg.json()
  go_new=d.get("id")
  pd=requests.post(f"{API}/items/{go_new}/description",headers=HJ,json={"plain_text":desc_go},timeout=20)
  print(f"\n✅ Go4 CLONED {go_new} qty={d.get('available_quantity')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")

# =========================================
# B) CHECK previous JBL Clip5 catalog status + publish variant CPID MLM37110751
# =========================================
print("\n=== B) JBL Clip 5 catalog variant ===")
# B1: status of previous catalog
prev="MLM3018313225"
gp=requests.get(f"{API}/items/{prev}?attributes=id,price,status,sub_status,available_quantity,sold_quantity,catalog_product_id",headers=H,timeout=15).json()
print(f"prev Clip5 negro: {gp}")

# B2: check CPID MLM37110751
for cpid in ["MLM37110181","MLM37110751"]:
  try:
    cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
    print(f"\nCPID {cpid}: name='{cp.get('name','?')[:80]}' domain={cp.get('domain_id')} pdp={cp.get('pdp_types')}")
    for a in cp.get("attributes",[])[:8]:
      print(f"  {a.get('id')}: {a.get('value_name')}")
  except Exception as e:
    print(f"err {cpid}: {e}")

# B3: publish the variant
CPID_VAR="MLM37110751"
TITLE_C5="Bocina Portátil JBL Clip 5 Bluetooth"  # generic since variant
payload_c5={
  "title": TITLE_C5,
  "catalog_product_id": CPID_VAR,
  "catalog_listing": True,
  "category_id":"MLM59800",
  "price":999,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_pro",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ]
}
pc=requests.post(f"{API}/items",headers=HJ,json=payload_c5,timeout=30)
print("\nClip5 variant POST:",pc.status_code)
print(pc.text[:1500])
if pc.status_code==201:
  d=pc.json()
  cid_new=d.get("id")
  print(f"\n✅ Clip5 variant CREATED {cid_new} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
