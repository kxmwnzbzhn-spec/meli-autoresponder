import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

# Source: Adrián
RT_A=os.environ["MELI_REFRESH_TOKEN_AH"]
ra=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_A},timeout=20)
AT_A=ra.json()["access_token"]
HA={"Authorization":f"Bearer {AT_A}"}

# Target: Mayrely
RT_M=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
rm=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_M},timeout=20)
print(f"Mayrely token: {rm.status_code}")
AT_M=rm.json()["access_token"]
HM={"Authorization":f"Bearer {AT_M}"}
HJM={"Authorization":f"Bearer {AT_M}","Content-Type":"application/json"}

# Verify Mayrely
me=requests.get(f"{API}/users/me",headers=HM,timeout=15).json()
print(f"Mayrely user_id: {me.get('id')}, nick: {me.get('nickname')}")

SRC="MLM2976325463"
src=requests.get(f"{API}/items/{SRC}",headers=HA,timeout=15).json()
print(f"\n=== SOURCE ===")
print(f"title: {src.get('title')}")
print(f"price: {src.get('price')}  qty: {src.get('available_quantity')}")
print(f"category: {src.get('category_id')}")
print(f"variations: {len(src.get('variations',[]))}")

# Re-upload pics to Mayrely (different seller)
src_pics=src.get("pictures",[])
print(f"src pics: {len(src_pics)}")
pic_ids=[]
for pp in src_pics[:10]:
  url=pp.get("secure_url") or pp.get("url")
  if not url: continue
  large=url.replace("-O.jpg","-F.jpg")
  for try_url in [large,url]:
    try:
      rr=requests.get(try_url,timeout=30)
      if rr.status_code==200 and len(rr.content)>10000:
        up=requests.post(f"{API}/pictures/items/upload",
          headers={"Authorization":f"Bearer {AT_M}"},
          files={"file":(f"bx_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
        if up.status_code in (200,201):
          pid=up.json().get("id")
          if pid: pic_ids.append(pid); print(f"  ✓ {pid}"); break
        else:
          print(f"  ✗ upload {up.status_code}: {up.text[:200]}"); break
    except Exception as e:
      print(f"  err: {e}")
print(f"uploaded: {len(pic_ids)}")

# Get desc
dr=requests.get(f"{API}/items/{SRC}/description",headers=HA,timeout=15)
desc=dr.json().get("plain_text","") if dr.status_code==200 else ""
print(f"desc len: {len(desc)}")

# Get variations
variations=[]
for v in src.get("variations",[]):
  # Each variation has attribute_combinations (e.g. SIZE) + price + available_quantity
  variations.append({
    "attribute_combinations": v.get("attribute_combinations",[]),
    "available_quantity": v.get("available_quantity") or 10,
    "price": v.get("price") or src.get("price"),
    "picture_ids": pic_ids[:3]  # reuse pics
  })
print(f"variations to clone: {len(variations)}")
for v in variations:
  combo=", ".join(f"{a.get('name')}={a.get('value_name')}" for a in v["attribute_combinations"])
  print(f"  {combo} | qty={v['available_quantity']} | $${v['price']}")

# Build attrs (exclude variation-controlling SIZE)
src_attrs=src.get("attributes",[])
keep={"BRAND","GENDER","AGE_GROUP","MAIN_MATERIAL","UNITS_PER_PACK","MAIN_COLOR","COLOR","ITEM_CONDITION","MODEL","LINE","CLOTHING_TYPE","UNDERWEAR_TYPE","PATTERN","DESIGN"}
attrs=[]
for a in src_attrs:
  aid=a.get("id")
  if aid in keep and (a.get("value_name") or a.get("value_id")) and aid!="SIZE":
    attrs.append({"id":aid,"value_name":a.get("value_name"),"value_id":a.get("value_id")})

# Build payload
payload={
  "title": src.get("title"),
  "category_id": src.get("category_id"),
  "price": src.get("price") or 399,
  "currency_id":"MXN",
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc[:5000]}
}
if variations:
  payload["variations"]=variations
else:
  payload["available_quantity"]=src.get("available_quantity") or 100

print(f"\nsending {len(attrs)} attrs, {len(pic_ids)} pics, {len(variations)} variations")
p=requests.post(f"{API}/items",headers=HJM,json=payload,timeout=30)
print(f"POST: {p.status_code}")
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJM,json={"plain_text":desc[:5000]},timeout=20)
  print(f"\n✅ CLONED to Mayrely: {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
