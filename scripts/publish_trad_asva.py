import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM75290480"

# Product info
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
name=p.get("name","?")
dom=p.get("domain_id","")
print(f"\n=== CPID {CPID} ===",flush=True)
print(f"  name: {name}",flush=True)
print(f"  domain: {dom}",flush=True)

# Decide category: if esoteric perfume -> MLM456032, else MLM1271
if "ESOTERIC" in dom.upper():
    cat="MLM456032"
elif "PERFUME" in dom.upper():
    cat="MLM1271"
else:
    cat="MLM1271"
print(f"  chosen cat: {cat}",flush=True)

# Get pics + attributes from CPID
pics=[{"source":pic.get("url")} for pic in p.get("pictures",[])[:8] if pic.get("url")]
print(f"  pics: {len(pics)}",flush=True)

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

# Ensure BRAND + MODEL present
has_brand=any(a["id"]=="BRAND" for a in new_attrs)
has_model=any(a["id"]=="MODEL" for a in new_attrs)
if not has_brand:
    new_attrs.append({"id":"BRAND","value_name":"The Alchemia Lab"})
if not has_model:
    # Extract from name
    mtoken=name.split("|")[0].replace("Perfume","").replace("The Alchemia Lab","").replace("Eau De Parfum","").replace("Eau de Parfum","").replace("100ml","").replace("100 Ml","").strip()
    new_attrs.append({"id":"MODEL","value_name":mtoken[:30] if mtoken else "Alchemia"})

# Title from name
title=name[:60]

payload={
    "family_name":title,
    "category_id":cat,
    "price":399,
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
print(f"\n=== POSTING TRADICIONAL cat={cat} attrs={len(new_attrs)} ===",flush=True)

post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in post:
    new_id=post["id"]
    print(f"\n✅ POSTED: {new_id} status={post.get('status')} cat={post.get('category_id')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
    print(f"  title: {post.get('title','?')[:80]}",flush=True)
    print(f"  URL: {post.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"\n❌ FAIL: {json.dumps(post)[:1800]}",flush=True)
