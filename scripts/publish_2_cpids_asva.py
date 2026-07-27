import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPIDS=["MLM75774569","MLM75774568"]
results=[]

for CPID in CPIDS:
    print(f"\n=== CPID {CPID} ===",flush=True)
    p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
    name=p.get("name","?")
    dom=p.get("domain_id","?")
    print(f"  name: {name[:90]}",flush=True)
    print(f"  domain: {dom}",flush=True)
    bbw=p.get("buy_box_winner") or {}
    bbw_price=bbw.get("price")
    print(f"  buy_box_winner: ${bbw_price}",flush=True)
    
    # Elegir categoría según dominio
    cat_id=None
    for a in p.get("attributes",[]):
        if a.get("id")=="ITEM_CATEGORY":
            cat_id=a.get("value_id"); break
    if not cat_id:
        if "ESOTERIC" in dom.upper() or "esoteric" in dom.lower():
            cat_id="MLM456032"
        elif "PERFUME" in dom.upper():
            cat_id="MLM1271"
        else:
            cat_id="MLM1271"
    print(f"  cat: {cat_id}",flush=True)
    
    price=int(bbw_price or 399)
    payload={
        "catalog_product_id":CPID,
        "category_id":cat_id,
        "price":price,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"new",
        "listing_type_id":"gold_pro",
        "catalog_listing":True,
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                      {"id":"WARRANTY_TIME","value_name":"30 días"}]
    }
    print(f"  posting: price=${price} cat={cat_id}",flush=True)
    post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
    if "id" in post:
        new_id=post["id"]
        print(f"  ✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
        print(f"  title: {post.get('title','?')[:80]}",flush=True)
        print(f"  URL: {post.get('permalink','?')}",flush=True)
        results.append((CPID,new_id,name[:60],price))
    else:
        print(f"  ❌ FAIL: {json.dumps(post)[:800]}",flush=True)
        results.append((CPID,None,name[:60],None))
    time.sleep(1)

# Save to Supabase
sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
for CPID,new_id,name,price in results:
    if not new_id: continue
    row={"item_id":new_id,"account":"ASVA","default_qty":1,"product_name":name,
         "reason":f"publicado catalog CPID {CPID} en ASVA 2026-07-21"}
    requests.post(f"{sb_url}/rest/v1/meli_priority_replenish",headers=sh,json=row,timeout=10)

requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.ASVA",headers=sh,json={"refresh_token":r["refresh_token"] if False else os.environ.get("_","")},timeout=10)

print(f"\n=== SUMMARY ===",flush=True)
for CPID,new_id,name,price in results:
    print(f"  {CPID} -> {new_id} ${price} | {name}",flush=True)
