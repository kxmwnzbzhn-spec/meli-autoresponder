import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPIDS=["MLM44710240","MLM68969359"]
results=[]
for CPID in CPIDS:
  print(f"\n=== {CPID} ===")
  cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
  name=cp.get("name","")
  print(f"  name: {name}")
  parent=cp.get("parent_id")
  print(f"  parent: {parent} pdp: {cp.get('pdp_types')}")
  
  # snapshot
  i=requests.get(f"{API}/products/{CPID}/items?limit=10",headers=H,timeout=15).json()
  ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
  ps.sort()
  if ps: print(f"  competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")
  
  TITLE=name[:60] if len(name)<=60 else "Bocina " + " ".join(name.split()[:8])
  TITLE=TITLE[:60]
  print(f"  title: '{TITLE}' ({len(TITLE)})")
  
  payload={
    "title": TITLE,
    "catalog_product_id":CPID,
    "catalog_listing":True,
    "category_id":"MLM59800",
    "price":599,
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
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  print(f"  POST catalog: {p.status_code}")
  if p.status_code==201:
    d=p.json()
    iid=d.get("id")
    print(f"  ✅ CATALOG CREATED {iid} @ ${d.get('price')}")
    print(f"  permalink: {d.get('permalink')}")
    results.append((CPID,iid,"catalog",d.get("permalink")))
  else:
    err=p.text[:500]
    print(f"  ERROR: {err}")
    # Fallback: tradicional with CPID
    if "seller.optin.fake" in err or "forbidden" in err:
      print("  → trying TRADICIONAL fallback")
      payload2=dict(payload)
      payload2.pop("catalog_listing",None)
      payload2["listing_type_id"]="gold_special"
      # gold_special tradicional requires pictures
      cp_pics=cp.get("pictures",[])[:6]
      pic_ids=[]
      for pp in cp_pics:
        url=pp.get("url","").replace("-O.jpg","-F.jpg")
        try:
          rr=requests.get(url,timeout=30)
          if rr.status_code==200 and len(rr.content)>10000:
            up=requests.post(f"{API}/pictures/items/upload",headers={"Authorization":f"Bearer {AT}"},
              files={"file":(f"go_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
            if up.status_code in (200,201):
              pid=up.json().get("id")
              if pid: pic_ids.append(pid)
        except: pass
      payload2["pictures"]=[{"id":x} for x in pic_ids]
      payload2["attributes"]=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Go 4"},
        {"id":"WITH_BLUETOOTH","value_name":"Sí"},
        {"id":"IS_WATER_RESISTANT","value_name":"Sí"},
        {"id":"GTIN","value_name":"6925281982989"},
      ]
      p2=requests.post(f"{API}/items",headers=HJ,json=payload2,timeout=30)
      print(f"  POST tradicional: {p2.status_code}")
      if p2.status_code==201:
        d=p2.json()
        iid=d.get("id")
        print(f"  ✅ TRADICIONAL CREATED {iid} @ ${d.get('price')}")
        print(f"  permalink: {d.get('permalink')}")
        results.append((CPID,iid,"tradicional",d.get("permalink")))
      else:
        print(f"  TRAD ERROR: {p2.text[:500]}")

print("\n=== SUMMARY ===")
for c,i,t,u in results:
  print(f"  {c} → {i} ({t}) @ $599")
  print(f"    {u}")
