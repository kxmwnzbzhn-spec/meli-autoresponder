import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

def refresh(rt_env):
    RT=os.environ[rt_env]
    r=requests.post("https://api.mercadolibre.com/oauth/token",
      data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
    return r["access_token"], r["refresh_token"]

AT_A, NEW_RT_A = refresh("MELI_REFRESH_TOKEN_ASVA")
AT_L, NEW_RT_L = refresh("MELI_REFRESH_TOKEN_LIGIA")
print(f"NEW_RT_ASVA: {NEW_RT_A}",flush=True)
print(f"NEW_RT_LIGIA: {NEW_RT_L}",flush=True)
H_A={"Authorization":f"Bearer {AT_A}","Content-Type":"application/json"}
H_L={"Authorization":f"Bearer {AT_L}","Content-Type":"application/json"}

SRC="MLM2952660425"
s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H_A,timeout=15).json()
print(f"\n=== SOURCE {SRC} (ASVA) ===",flush=True)
print(f"  title: {s.get('title','?')[:80]}",flush=True)
print(f"  cat: {s.get('category_id')}  price: ${s.get('price')}  qty: {s.get('available_quantity')}",flush=True)
print(f"  cpid: {s.get('catalog_product_id')}",flush=True)
print(f"  listing_type: {s.get('listing_type_id')}",flush=True)
print(f"  condition: {s.get('condition')}",flush=True)
print(f"  family: {s.get('family_name')}",flush=True)

CPID=s.get("catalog_product_id")
cat=s.get("category_id")
price=s.get("price") or 399
qty=s.get("available_quantity") or 1
listing=s.get("listing_type_id") or "gold_pro"
condition=s.get("condition") or "new"
family=s.get("family_name") or s.get("title")

if CPID:
    # Catalog listing
    payload={
        "catalog_product_id":CPID,
        "category_id":cat,
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
    print(f"\n=== POSTING CATALOG on LIGIA cpid={CPID} cat={cat} ===",flush=True)
else:
    # Traditional
    BAD={"ALPHANUMERIC_MODEL","HAZMAT_TRANSPORTABILITY","SELLER_SKU","ITEM_CONDITION","GTIN","EAN","UPC","ISBN","CATALOG_PRODUCT_ID","PACKAGE_WEIGHT","PACKAGE_LENGTH","PACKAGE_HEIGHT","PACKAGE_WIDTH"}
    def pic_url(p):
        for k in ("secure_url","url","source"):
            if p.get(k): return p[k]
    pics=[pic_url(p) for p in s.get("pictures",[])[:10]]
    pics=[u for u in pics if u]
    
    new_attrs=[]
    seen=set()
    for a in s.get("attributes",[]):
        aid=a.get("id","")
        if aid in BAD or aid in seen: continue
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
        "category_id":cat,
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
    print(f"\n=== POSTING TRADICIONAL on LIGIA cat={cat} attrs={len(new_attrs)} ===",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H_L,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED on LIGIA: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
    
    # Copy description
    d=requests.get(f"https://api.mercadolibre.com/items/{SRC}/description",headers=H_A,timeout=10).json()
    if d.get("plain_text"):
        r=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H_L,json={"plain_text":d["plain_text"]},timeout=15)
        print(f"  description: {r.status_code}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:1500]}",flush=True)
