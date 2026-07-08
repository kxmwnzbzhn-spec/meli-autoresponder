import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM75022568"
NEW_CAT="MLM456032"  # Esotericos > Perfumes

# Get CPID details for pics and attributes
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=15).json()
title=p.get("name","Perfume Flor de Nopal Alchemia Lab")[:60]
print(f"CPID name: {title}",flush=True)

pics=[{"source":pic.get("url")} for pic in p.get("pictures",[])[:8] if pic.get("url")]
print(f"  pics: {len(pics)}",flush=True)

# Extract attrs from CPID
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
new_attrs.append({"id":"MODEL","value_name":"Flor de Nopal"})
print(f"  attrs: {len(new_attrs)}",flush=True)

payload={
    
    "family_name":title,
    "category_id":NEW_CAT,
    "price":999,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_pro",
    "pictures":pics,
    "attributes":new_attrs,
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                  {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print(f"\n=== POSTING TRADICIONAL cat={NEW_CAT} ===",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id} status={post.get('status')} cat={post.get('category_id')} price=${post.get('price')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
    
    # Copy description from the old MLM5655369246 or from CPID
    for src_id in ("MLM3100147427","MLM5655369246"):
        d=requests.get(f"https://api.mercadolibre.com/items/{src_id}/description",headers=H,timeout=10).json()
        if d.get("plain_text"):
            r=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                           headers=H,json={"plain_text":d["plain_text"]},timeout=15)
            print(f"  description from {src_id}: {r.status_code}",flush=True)
            break
    
    # Close the old catalog_listing one
    print(f"\n=== CLOSING MLM3100147427 (catalog_listing) ===",flush=True)
    # under_review might not be closeable directly, try pause first
    for status in ("paused","closed"):
        r=requests.put(f"https://api.mercadolibre.com/items/MLM3100147427",headers=H,json={"status":status},timeout=10).json()
        print(f"  {status}: {r.get('status')} err={r.get('error','')}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:2000]}",flush=True)
