import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

TARGET_CAT="MLM456032"  # Otras Categorías > Esoterismo > Perfumes

# Dedupe list of CPIDs from user (skip Flor de Nopal MLM52113823 = already published as MLM3035329049)
CPIDS=[
  "MLM52129273","MLM52129383",
  "MLM69794978","MLM70112010","MLM70063829","MLM70063831","MLM70063753",
  "MLM70064197","MLM70063779","MLM70063764","MLM70063872","MLM70063777",
  "MLM69963991","MLM69794800","MLM69794759","MLM69794771","MLM69794753",
  "MLM69794803","MLM69795006","MLM69794809","MLM69794761","MLM69795042",
  "MLM69795023","MLM69795002","MLM70246385","MLM70246250","MLM70246080",
  "MLM70245995","MLM70245790",
  "MLM62653473","MLM62651426","MLM62628964","MLM62627264"
]
print(f"CPIDs to publish: {len(CPIDS)}")

# Find required attributes for category
ats=requests.get(f"{API}/categories/{TARGET_CAT}/attributes",headers=H,timeout=15).json()
valid={a["id"]:a for a in ats}

results=[]
for cpid in CPIDS:
  print(f"\n=== {cpid} ===")
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  name=cp.get("name","")
  print(f"  name: {name[:80]}")
  
  TITLE=(name or "Perfume The Alchemia Lab")[:60]
  
  # Upload photos from CPID
  pic_ids=[]
  for p in cp.get("pictures",[])[:6]:
    url=(p.get("url") or "").replace("-O.jpg","-F.jpg")
    try:
      rr=requests.get(url,timeout=30)
      if rr.status_code==200 and len(rr.content)>10000:
        up=requests.post(f"{API}/pictures/items/upload",headers={"Authorization":f"Bearer {AT}"},
          files={"file":(f"{cpid}_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
        if up.status_code in (200,201):
          pid=up.json().get("id")
          if pid: pic_ids.append(pid)
    except: pass
  print(f"  pics: {len(pic_ids)}")
  
  # Get description suggested by CPID/title
  short=name.split(" | ")[0] if " | " in name else name
  perfume_brief=name.split(" | ")[1][:200] if " | " in name else ""
  desc=(f"{short}\n\n"
        f"{perfume_brief}\n\n"
        f"Eau de Parfum 100ml unisex. Producto original The Alchemia Lab. "
        f"Perfumería artesanal mexicana. Envío inmediato. Garantía del vendedor 30 días.")
  
  # Attributes
  attrs=[]
  for aid,name_def in [
    ("BRAND","The Alchemia Lab"),
    ("ITEM_CONDITION","Nuevo"),
    ("GENDER","Sin género"),
    ("UNIT_VOLUME","100 mL"),
    ("FRAGRANCE_TYPE","Eau de parfum"),
    ("PERFUME_NAME", short.replace("Perfume ","").split(" The Alchemia")[0]),
    ("MODEL", short.replace("Perfume ","").split(" The Alchemia")[0]),
  ]:
    if aid in valid:
      attrs.append({"id":aid,"value_name":name_def})
  
  payload={
    "family_name": TITLE,
    "category_id": TARGET_CAT,
    "price": 999,
    "currency_id":"MXN",
    "available_quantity":50,
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
    "description":{"plain_text":desc}
  }
  
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  if p.status_code==201:
    d=p.json()
    new_id=d.get("id")
    requests.post(f"{API}/items/{new_id}/description",headers=HJ,json={"plain_text":desc},timeout=20)
    print(f"  ✅ {new_id} @ ${d.get('price')} status={d.get('status')}")
    print(f"  permalink: {d.get('permalink')}")
    results.append((cpid,new_id,short[:50]))
  else:
    print(f"  ❌ {p.status_code} {p.text[:400]}")
  time.sleep(0.4)

print("\n\n=== SUMMARY ===")
for c,i,t in results:
  print(f"  {c} → {i} | {t}")
print(f"\n✅ Total publicados: {len(results)}/{len(CPIDS)}")
