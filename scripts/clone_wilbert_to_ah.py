import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

# Wilbert token (source)
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
rw=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_W},timeout=20)
AT_W=rw.json()["access_token"]
HW={"Authorization":f"Bearer {AT_W}"}

# Adrián token (target)
RT_A=os.environ["MELI_REFRESH_TOKEN_AH"]
ra=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_A},timeout=20)
AT_A=ra.json()["access_token"]
HA={"Authorization":f"Bearer {AT_A}"}
HJA={"Authorization":f"Bearer {AT_A}","Content-Type":"application/json"}

SRC="MLM2911241921"
src=requests.get(f"{API}/items/{SRC}",headers=HW,timeout=15).json()
print(f"src title: {src.get('title')}")
print(f"src price: {src.get('price')}")
print(f"src category: {src.get('category_id')}")
print(f"src CPID: {src.get('catalog_product_id')}")
print(f"src condition: {src.get('condition')}")
print(f"src pics: {len(src.get('pictures',[]))}")
print(f"src attrs: {len(src.get('attributes',[]))}")

src_pics=src.get("pictures",[])
# Re-upload pics to Adrián
pic_ids=[]
for pp in src_pics[:10]:
  url=pp.get("secure_url") or pp.get("url")
  if not url: continue
  try:
    rr=requests.get(url,timeout=30)
    if rr.status_code==200 and len(rr.content)>5000:
      up=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT_A}"},
        files={"file":(f"c_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
      if up.status_code in (200,201):
        pid=up.json().get("id")
        if pid: pic_ids.append(pid); print(f"  ✓ {pid}")
  except Exception as e:
    print(f"  err: {e}")
print(f"\nuploaded pics: {len(pic_ids)}")

# Get description from Wilbert
sd=requests.get(f"{API}/items/{SRC}/description",headers=HW,timeout=15)
src_desc=""
if sd.status_code==200:
  src_desc=sd.json().get("plain_text","") or ""
print(f"desc len: {len(src_desc)}")

TITLE=(src.get("title") or "")[:60]
CAT=src.get("category_id") or "MLM59800"
CPID=src.get("catalog_product_id")
COND=src.get("condition") or "used"

SAFE_KEEP=["BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","GTIN","CONNECTION_TYPE","DETAILED_MODEL","SERIES"]
attrs=[]
for a in (src.get("attributes") or []):
  if a.get("id") in SAFE_KEEP and a.get("value_name"):
    attrs.append({"id":a["id"],"value_name":a["value_name"]})
# Force GTIN if missing
if not any(a["id"]=="GTIN" for a in attrs):
  attrs.append({"id":"GTIN","value_name":"6925281987564"})  # JBL Charge 6 GTIN

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": 599,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition": COND,
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
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

print(f"\nsending {len(attrs)} attrs, pics={len(pic_ids)}, cond={COND}, CPID={CPID}, cat={CAT}")
p=requests.post(f"{API}/items",headers=HJA,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  if src_desc:
    pd=requests.post(f"{API}/items/{iid}/description",headers=HJA,json={"plain_text":src_desc[:5000]},timeout=20)
    print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CLONED {iid} @ ${d.get('price')} cond={d.get('condition')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
