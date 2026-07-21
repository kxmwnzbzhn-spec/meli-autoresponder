import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

def refresh(env_var):
    RT=os.environ[env_var]
    r=requests.post("https://api.mercadolibre.com/oauth/token",
      data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
    return r["access_token"], r["refresh_token"]

AT_K, NEW_RT_K = refresh("MELI_REFRESH_TOKEN_KARIME")
AT_L, NEW_RT_L = refresh("MELI_REFRESH_TOKEN_LIGIA")
print(f"NEW_RT_KARIME: {NEW_RT_K}",flush=True)
print(f"NEW_RT_LIGIA: {NEW_RT_L}",flush=True)
H_K={"Authorization":f"Bearer {AT_K}","Content-Type":"application/json"}
H_L={"Authorization":f"Bearer {AT_L}","Content-Type":"application/json"}

SOURCES=[("MLM3129467021","Negra"),("MLM3129476561","Celeste")]
BAD_ATTRS={"ALPHANUMERIC_MODEL","HAZMAT_TRANSPORTABILITY","SELLER_SKU","ITEM_CONDITION","GTIN","EAN","UPC","ISBN","CATALOG_PRODUCT_ID","PACKAGE_WEIGHT","PACKAGE_LENGTH","PACKAGE_HEIGHT","PACKAGE_WIDTH"}

def pic_url(p):
    for k in ("secure_url","url","source"):
        if p.get(k): return p[k]

results=[]
for src,color in SOURCES:
    print(f"\n=== SOURCE {src} ({color}) ===",flush=True)
    s=requests.get(f"https://api.mercadolibre.com/items/{src}",headers=H_K,timeout=15).json()
    title=s.get("title","?")[:60]
    cat=s.get("category_id")
    price=int(s.get("price") or 299)
    qty=int(s.get("available_quantity") or 100)
    fam=s.get("family_name") or title
    print(f"  title: {title}",flush=True)
    print(f"  cat: {cat} price: ${price} qty: {qty} family: {fam[:40]}",flush=True)
    
    pics_raw=s.get("pictures",[])
    pics=[pic_url(p) for p in pics_raw[:10]]
    pics=[u for u in pics if u]
    print(f"  pics: {len(pics)}",flush=True)
    
    attrs_src=s.get("attributes",[])
    new_attrs=[]; seen=set()
    for a in attrs_src:
        aid=a.get("id","")
        if aid in BAD_ATTRS or aid in seen: continue
        v_id=a.get("value_id"); v_name=a.get("value_name")
        if (not v_id) and (not v_name or v_name in ("null","Null","NULL")): continue
        if v_id and not v_name: continue
        seen.add(aid)
        e={"id":aid}
        if v_id: e["value_id"]=v_id
        if v_name: e["value_name"]=v_name
        new_attrs.append(e)
    new_attrs.append({"id":"ITEM_CONDITION","value_name":"Usado"})
    print(f"  attrs: {len(new_attrs)}",flush=True)
    
    payload={
      "family_name":fam,
      "category_id":cat,
      "price":price,
      "currency_id":"MXN",
      "available_quantity":qty,
      "buying_mode":"buy_it_now",
      "condition":"used",
      "listing_type_id":s.get("listing_type_id","gold_pro"),
      "pictures":[{"source":u} for u in pics],
      "attributes":new_attrs,
      "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                    {"id":"WARRANTY_TIME","value_name":"30 días"}],
      "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
    }
    
    p=requests.post("https://api.mercadolibre.com/items",headers=H_L,json=payload,timeout=25).json()
    if "id" in p:
        new_id=p["id"]
        print(f"  ✅ POSTED LIGIA: {new_id} status={p.get('status')} price=${p.get('price')} qty={p.get('available_quantity')}",flush=True)
        print(f"  title: {p.get('title','?')[:70]}",flush=True)
        print(f"  URL: {p.get('permalink','?')}",flush=True)
        
        # Copy description
        d=requests.get(f"https://api.mercadolibre.com/items/{src}/description",headers=H_K,timeout=10).json()
        if d.get("plain_text"):
            r=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                           headers=H_L,json={"plain_text":d["plain_text"]},timeout=15)
            print(f"  description copied: {r.status_code}",flush=True)
        results.append((src,color,new_id))
    else:
        print(f"  ❌ FAIL: {json.dumps(p)[:1500]}",flush=True)
        results.append((src,color,None))
    time.sleep(1)

# Save to Supabase priority_replenish + rotate tokens
sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
for src,color,new_id in results:
    if not new_id: continue
    row={"item_id":new_id,"account":"LIGIA","default_qty":100,
         "product_name":f"Bocina Go 4 Reacondicionada {color} (clon KARIME {src})",
         "reason":"clonado KARIME->LIGIA 2026-07-21 con autostock qty=100"}
    requests.post(f"{sb_url}/rest/v1/meli_priority_replenish",headers=sh,json=row,timeout=10)
requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.KARIME",headers=sh,json={"refresh_token":NEW_RT_K},timeout=10)
requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.LIGIA",headers=sh,json={"refresh_token":NEW_RT_L},timeout=10)

print(f"\n=== SUMMARY ===",flush=True)
for src,color,new_id in results:
    print(f"  {src} ({color}) -> {new_id}",flush=True)
