import os, requests, time, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_ANGEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_ANGEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

# 20 IDs the user wants republished as CATALOG
TARGETS=["MLM5047369636","MLM2806516897","MLM5047380790","MLM2806516505","MLM2806514437","MLM2806512167","MLM5047370382","MLM5047367158","MLM2806503083","MLM2806518457","MLM5047371876","MLM5047368490","MLM2806505831","MLM5047380526","MLM5047380360","MLM5047379494","MLM2804079537","MLM2806516387","MLM2806518883","MLM5047378356"]

# --- PART 1: ensure these 20 are CLOSED before relisting (otherwise relist may dup) ---
print("\n--- Closing target 20 if not already ---")
for sid in TARGETS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    st=g.get("status")
    if st in ("closed","inactive"):
        print(f"  {sid} already {st}")
    else:
        if st in ("active","under_review","paused","programmed"):
            requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"paused"},timeout=20)
        rc=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"closed"},timeout=20)
        print(f"  {sid} close: {rc.status_code}")
        time.sleep(0.8)
    time.sleep(0.4)

# --- PART 2: republish each as catalog listing ---
print("\n--- Republishing 20 as catalog ---")
created=[]
for i,src_id in enumerate(TARGETS,1):
    src=requests.get(f"{API}/items/{src_id}",headers=H,timeout=20).json()
    cpid=src.get("catalog_product_id")
    if not cpid:
        # try to lookup via catalog matching for items that aren't catalog
        print(f"  [{i}/20] {src_id} no cpid (tradicional) -- republicare como tradicional con condition=new")
        # tradicional payload
        payload={
            "title": src.get("title"),
            "category_id": src.get("category_id"),
            "price": src.get("price"),
            "currency_id": src.get("currency_id","MXN"),
            "available_quantity": max(src.get("available_quantity") or 1, 1),
            "buying_mode": "buy_it_now",
            "condition": "new",
            "listing_type_id": src.get("listing_type_id","gold_special"),
            "description": {"plain_text": "Producto 100% original. Sellado de fábrica. Envío inmediato."},
            "pictures": [{"source": p["secure_url"]} for p in (src.get("pictures") or [])][:10],
            "attributes": [{"id":a["id"],"value_name":a.get("value_name")} for a in (src.get("attributes") or []) if a.get("value_name")],
        }
        r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    else:
        # catalog payload
        payload={
            "catalog_product_id": cpid,
            "catalog_listing": True,
            "site_id": "MLM",
            "currency_id": "MXN",
            "price": src.get("price"),
            "available_quantity": max(src.get("available_quantity") or 1, 1),
            "buying_mode": "buy_it_now",
            "condition": "new",
            "listing_type_id": "gold_pro",
            "sale_terms": [{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                           {"id":"WARRANTY_TIME","value_name":"30 días"}]
        }
        r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        created.append((src_id, d["id"], d.get("status"), d.get("price")))
        print(f"  [{i}/20] {src_id} -> NEW {d['id']} status={d.get('status')} price={d.get('price')} title='{(d.get('title') or '')[:60]}'")
    else:
        print(f"  [{i}/20] {src_id} ERR {r.status_code} {r.text[:250]}")
    time.sleep(1.2)

print("\n=== SUMMARY ===")
for src,nu,st,pr in created:
    print(f"  {src} -> {nu} {st} ${pr}")
print(f"total_new={len(created)}/{len(TARGETS)}")
