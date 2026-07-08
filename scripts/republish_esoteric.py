import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SRC="MLM5655369246"
NEW_CAT="MLM456032"  # Perfumes Esotericos

s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
print(f"\n=== SOURCE {SRC} ===",flush=True)
print(f"  title: {s.get('title','?')[:80]}",flush=True)
print(f"  cat: {s.get('category_id')}  price: ${s.get('price')}  qty: {s.get('available_quantity')}",flush=True)
print(f"  cpid: {s.get('catalog_product_id')}",flush=True)
print(f"  status: {s.get('status')}",flush=True)
print(f"  listing_type: {s.get('listing_type_id')}",flush=True)
print(f"  condition: {s.get('condition')}",flush=True)
print(f"  family_name: {s.get('family_name')}",flush=True)

CPID=s.get("catalog_product_id")
price=s.get("price") or 399
qty=s.get("available_quantity") or 1
listing=s.get("listing_type_id") or "gold_pro"
condition=s.get("condition") or "new"
family=s.get("family_name") or s.get("title")

# If CPID exists, use catalog_listing pattern
if CPID:
    payload={
        "catalog_product_id":CPID,
        "category_id":NEW_CAT,
        "price":price,
        "currency_id":"MXN",
        "available_quantity":qty,
        "buying_mode":"buy_it_now",
        "condition":condition,
        "listing_type_id":listing,
        "catalog_listing":True,
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                      {"id":"WARRANTY_TIME","value_name":"30 días"}]
    }
    print(f"\n=== POSTING CATALOG === cpid={CPID} cat={NEW_CAT}",flush=True)
else:
    # Traditional
    BAD_ATTRS={"ALPHANUMERIC_MODEL","HAZMAT_TRANSPORTABILITY","SELLER_SKU","ITEM_CONDITION","GTIN","EAN","UPC","ISBN","CATALOG_PRODUCT_ID"}
    def pic_url(p):
        for k in ("secure_url","url","source"):
            if p.get(k): return p[k]
    pics=[pic_url(p) for p in s.get("pictures",[])[:10]]
    pics=[u for u in pics if u]
    
    attrs_src=s.get("attributes",[])
    new_attrs=[]
    seen=set()
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
    new_attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo" if condition=="new" else "Usado"})
    
    payload={
        "family_name":family,
        "category_id":NEW_CAT,
        "price":price,
        "currency_id":"MXN",
        "available_quantity":qty,
        "buying_mode":"buy_it_now",
        "condition":condition,
        "listing_type_id":listing,
        "pictures":[{"source":u} for u in pics],
        "attributes":new_attrs,
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                      {"id":"WARRANTY_TIME","value_name":"30 días"}]
    }
    print(f"\n=== POSTING TRADITIONAL === cat={NEW_CAT} attrs={len(new_attrs)}",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    
    # Try to copy description
    desc_src=requests.get(f"https://api.mercadolibre.com/items/{SRC}/description",headers=H,timeout=10).json()
    if desc_src.get("plain_text"):
        d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H,json={"plain_text":desc_src["plain_text"]},timeout=15)
        print(f"  description copied: {d.status_code}",flush=True)
    
    print(f"NEW_ITEM_ID={new_id}",flush=True)
    
    # Close original
    print(f"\n=== CLOSING ORIGINAL {SRC} ===",flush=True)
    if s.get("status")=="active":
        pp=requests.put(f"https://api.mercadolibre.com/items/{SRC}",headers=H,json={"status":"paused"},timeout=10).json()
        print(f"  paused: {pp.get('status')}",flush=True)
    cc=requests.put(f"https://api.mercadolibre.com/items/{SRC}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"  closed: {cc.get('status')}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:1500]}",flush=True)
