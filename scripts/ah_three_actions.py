import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

# Action 1: MLM2969827031 → $899
print("\n=== Action 1: MLM2969827031 price=$899 ===")
g=requests.get(f"{API}/items/MLM2969827031",headers=H,timeout=15).json()
print(f"BEFORE: status={g.get('status')} price=${g.get('price')} title={(g.get('title') or '')[:50]}")
r=requests.put(f"{API}/items/MLM2969827031",headers=HJ,json={"price":899},timeout=20)
print(f"PUT $899: {r.status_code} {r.text[:120] if r.status_code>=400 else 'OK'}")
g2=requests.get(f"{API}/items/MLM2969827031",headers=H,timeout=15).json()
print(f"AFTER: price=${g2.get('price')}")

# Action 2: MLM2969827263 → close catalog + republish tradicional
print("\n=== Action 3: MLM2969827263 close+republish as tradicional ===")
SRC="MLM2969827263"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=20).json()
title=(src.get("title") or "")[:60]
cat=src.get("category_id")
price=src.get("price")
pictures=[{"source":p["secure_url"]} for p in (src.get("pictures") or [])][:10]
print(f"SOURCE: {SRC} status={src.get('status')} price=${price} title={title}")
print(f"  category={cat} cpid={src.get('catalog_product_id')} pictures={len(pictures)}")

# Build attrs (keep all except those that conflict with non-catalog)
attrs=[]
for a in (src.get("attributes") or []):
    aid=a.get("id")
    if aid in ("SELLER_SKU","DETAILED_MODEL","IS_GAMER"): continue
    if not (a.get("value_name") or a.get("value_id")): continue
    o={"id":aid}
    if a.get("value_id"): o["value_id"]=a["value_id"]
    if a.get("value_name"): o["value_name"]=a["value_name"]
    attrs.append(o)
print(f"  attrs to transfer: {len(attrs)}")

# Close catalog first
print(f"\nClosing catalog listing {SRC}...")
if src.get("status")=="active":
    requests.put(f"{API}/items/{SRC}",headers=HJ,json={"status":"paused"},timeout=20)
    time.sleep(0.5)
rc=requests.put(f"{API}/items/{SRC}",headers=HJ,json={"status":"closed"},timeout=20)
print(f"  close: {rc.status_code}")
time.sleep(0.5)
rd=requests.put(f"{API}/items/{SRC}",headers=HJ,json={"deleted":"true"},timeout=20)
print(f"  del-flag: {rd.status_code}")

# Republish as tradicional
print(f"\nPublishing TRADITIONAL...")
payload={
    "site_id":"MLM","title":title,"category_id":cat,
    "price":price,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_special","condition":"new",
    "description":{"plain_text":"Producto original. Sellado de fábrica. Envío inmediato."},
    "pictures":pictures,
    "attributes":attrs,
    "shipping":{"mode":"me2","free_shipping":False}
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"POST tradicional: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"✓ NEW TRADICIONAL: {d['id']} status={d.get('status')} ${d.get('price')}")
    print(f"  url={d.get('permalink')}")
else:
    print(f"✗ FAIL: {r.text[:500]}")
