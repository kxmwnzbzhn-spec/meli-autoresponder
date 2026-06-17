import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SRC="MLM2911241921"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"src title: {src.get('title')}")
print(f"src price: {src.get('price')}")
print(f"src category: {src.get('category_id')}")
print(f"src CPID: {src.get('catalog_product_id')}  catalog_listing: {src.get('catalog_listing')}")
print(f"src condition: {src.get('condition')}")
print(f"src seller: {src.get('seller_id')}")
print(f"src status: {src.get('status')}  pics: {len(src.get('pictures',[]))}  attrs: {len(src.get('attributes',[]))}")

# Get pictures
src_pics=src.get("pictures",[])
src_seller=src.get("seller_id")
my_seller=3417664339  # Adrián

# Try direct ID reuse first if same seller, otherwise reupload
pic_ids_to_use=[]
if src_seller==my_seller:
  pic_ids_to_use=[p.get("id") for p in src_pics if p.get("id")]
  print(f"\nsame seller → reusing {len(pic_ids_to_use)} pic IDs")
else:
  print(f"\ndifferent seller ({src_seller}) → re-uploading pics")
  for pp in src_pics[:10]:
    url=pp.get("secure_url") or pp.get("url")
    if not url: continue
    try:
      rr=requests.get(url,timeout=30)
      if rr.status_code==200 and len(rr.content)>5000:
        up=requests.post(f"{API}/pictures/items/upload",
          headers={"Authorization":f"Bearer {AT}"},
          files={"file":(f"c_{len(pic_ids_to_use)}.jpg",rr.content,"image/jpeg")},timeout=60)
        if up.status_code in (200,201):
          pid=up.json().get("id")
          if pid: pic_ids_to_use.append(pid); print(f"  ✓ {pid}")
    except Exception as e:
      print(f"  err: {e}")
  print(f"re-uploaded: {len(pic_ids_to_use)}")

# Description
sd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=15).json()
src_desc=sd.get("plain_text") or sd.get("text") or ""
print(f"src desc len: {len(src_desc)}")

# Build clone payload
TITLE=src.get("title","")[:60]
CAT=src.get("category_id")
CPID=src.get("catalog_product_id")
COND=src.get("condition") or "new"

src_attrs=src.get("attributes",[])
# only safe attrs
SAFE_KEEP=["BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","GTIN","CONNECTION_TYPE","DETAILED_MODEL","SERIES"]
attrs=[]
for a in src_attrs:
  if a.get("id") in SAFE_KEEP and a.get("value_name"):
    attrs.append({"id":a["id"],"value_name":a["value_name"]})

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": 599,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition": COND,
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids_to_use],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":src_desc[:5000] if src_desc else TITLE}
}
if CPID:
  payload["catalog_product_id"]=CPID

print(f"\nsending {len(attrs)} attrs, pics={len(pic_ids_to_use)}, condition={COND}, CPID={CPID}")
p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  if src_desc:
    pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":src_desc[:5000]},timeout=20)
    print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CLONED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
