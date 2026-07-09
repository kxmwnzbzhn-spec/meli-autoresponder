import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SRC="MLM5648924482"  # catalog_listing Tlaloc
NEW_CAT="MLM456032"  # Esotericos > Perfumes

# Get source details
s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
print(f"\n=== SOURCE {SRC} ===",flush=True)
print(f"  title: {s.get('title','?')[:80]}",flush=True)
print(f"  cat: {s.get('category_id')}  price: ${s.get('price')}  qty: {s.get('available_quantity')}",flush=True)
print(f"  cpid: {s.get('catalog_product_id')}",flush=True)

CPID=s.get("catalog_product_id")
price=s.get("price") or 399
qty=s.get("available_quantity") or 1

# Get CPID details for pics and attributes (best source)
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=15).json()
title=p.get("name","Perfume Tláloc Alchemia Lab")[:60]
pics=[{"source":pic.get("url")} for pic in p.get("pictures",[])[:8] if pic.get("url")]
print(f"  CPID name: {title}  pics: {len(pics)}",flush=True)

BAD={"ITEM_CONDITION","GTIN","EAN","UPC","ITEM_CATEGORY","CATALOG_PRODUCT_ID","ALPHANUMERIC_MODEL"}
new_attrs=[]
seen=set()
for a in p.get("attributes",[]):
    aid=a.get("id","")
    if aid in BAD or aid in seen: continue
    v_id=a.get("value_id"); v_name=a.get("value_name")
    if (not v_id) and (not v_name): continue
    seen.add(aid)
    e={"id":aid}
    if v_id: e["value_id"]=v_id
    if v_name: e["value_name"]=v_name
    new_attrs.append(e)
new_attrs.append({"id":"ITEM_CONDITION","value_name":"Nuevo"})
new_attrs.append({"id":"BRAND","value_name":"The Alchemia Lab"})
new_attrs.append({"id":"MODEL","value_name":"Tláloc Intenso"})
print(f"  attrs: {len(new_attrs)}",flush=True)

payload={
    "family_name":title,
    "category_id":NEW_CAT,
    "price":price,
    "currency_id":"MXN",
    "available_quantity":qty,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "pictures":pics,
    "attributes":new_attrs,
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                  {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print(f"\n=== POSTING TRADICIONAL cat={NEW_CAT} price=${price} qty={qty} ===",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id} status={post.get('status')} cat={post.get('category_id')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
    
    # Copy description from source
    d=requests.get(f"https://api.mercadolibre.com/items/{SRC}/description",headers=H,timeout=10).json()
    if d.get("plain_text"):
        r=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                       headers=H,json={"plain_text":d["plain_text"]},timeout=15)
        print(f"  description copied: {r.status_code}",flush=True)
    
    # Close original catalog
    print(f"\n=== CLOSING catalog original {SRC} ===",flush=True)
    if s.get("status")=="active":
        pp=requests.put(f"https://api.mercadolibre.com/items/{SRC}",headers=H,json={"status":"paused"},timeout=10).json()
        print(f"  paused: {pp.get('status')} err={pp.get('error','')}",flush=True)
    cc=requests.put(f"https://api.mercadolibre.com/items/{SRC}",headers=H,json={"status":"closed"},timeout=10).json()
    print(f"  closed: {cc.get('status')} err={cc.get('error','')}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:1800]}",flush=True)
