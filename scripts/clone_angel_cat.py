import os, requests, time
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

TARGETS=["MLM5047369636","MLM2806516897","MLM5047380790","MLM2806516505","MLM2806514437","MLM2806512167","MLM5047370382","MLM5047367158","MLM2806503083","MLM2806518457","MLM5047371876","MLM5047368490","MLM2806505831","MLM5047380526","MLM5047380360","MLM5047379494","MLM2804079537","MLM2806516387","MLM2806518883","MLM5047378356"]

created=[]
fail=[]
for i,src_id in enumerate(TARGETS,1):
    src=requests.get(f"{API}/items/{src_id}",headers=H,timeout=20).json()
    cpid=src.get("catalog_product_id")
    title=(src.get("title") or "")[:60]
    cat=src.get("category_id")
    price=src.get("price")
    if not cpid:
        # MLM2804079537 didn't have cpid (tradicional). Publish as tradicional condition:new
        payload={
            "site_id":"MLM","title":title,"category_id":cat,"price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_special",
            "condition":"new",
            "description":{"plain_text":"Producto 100% original. Envío inmediato."},
            "pictures":[{"source":p["secure_url"]} for p in (src.get("pictures") or [])][:10],
            "attributes":[{"id":a["id"],"value_name":a.get("value_name")} for a in (src.get("attributes") or []) if a.get("value_name")],
            "shipping":{"mode":"me2","free_shipping":False}
        }
    else:
        payload={
            "site_id":"MLM","title":title,"category_id":cat,"price":price,"currency_id":"MXN",
            "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
            "condition":"new","catalog_product_id":cpid,"catalog_listing":True,
            "shipping":{"mode":"me2","free_shipping":True}
        }
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        created.append((src_id,d["id"],d.get("status"),d.get("price")))
        print(f"  [{i}/20] {src_id} -> {d['id']} status={d.get('status')} ${d.get('price')} '{title[:55]}'")
    else:
        # try fallback without free_shipping if me2 not allowed
        if "shipping" in (r.text or "").lower() or "me2" in (r.text or "").lower():
            payload["shipping"]={"mode":"not_specified"}
            r2=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
            if r2.status_code in (200,201):
                d=r2.json()
                created.append((src_id,d["id"],d.get("status"),d.get("price")))
                print(f"  [{i}/20] {src_id} -> {d['id']} (no_ship) status={d.get('status')} ${d.get('price')}")
                time.sleep(1.2); continue
        fail.append((src_id,r.status_code,r.text[:400]))
        print(f"  [{i}/20] {src_id} ERR {r.status_code} {r.text[:300]}")
    time.sleep(1.2)

print(f"\n=== RESUMEN ===")
print(f"OK={len(created)} FAIL={len(fail)}")
for s,n,st,pr in created: print(f"  OK {s} -> {n} {st} ${pr}")
for s,c,t in fail: print(f"  FAIL {s} [{c}]: {t[:200]}")
