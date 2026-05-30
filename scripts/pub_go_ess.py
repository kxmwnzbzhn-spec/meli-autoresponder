"""Publica 2 Go Essential 2 (Azul + Rojo) en Claribel, 1pza, no auto-replenish.
Azul URL: /up/MLMU3974334644 wid=MLM2932066457 → resolver para sacar cpid
Rojo URL: /p/MLM63638533 (cpid directo)
"""
import os, requests, time, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]

# Resolve Azul cpid from wid
print("\n=== Resolve AZUL ===")
azul_wid="MLM2932066457"
src=requests.get(f"{API}/items/{azul_wid}",headers=H,timeout=15).json()
azul_cpid=src.get("catalog_product_id")
azul_title=(src.get("title") or "JBL Go Essential 2 Azul")[:60]
print(f"  wid={azul_wid} cpid={azul_cpid} title={azul_title}")

# Si no tiene cpid, buscar JBL Go Essential 2 Azul en catalog
if not azul_cpid:
    print("  no direct cpid — searching catalog for Go Essential 2 Azul")
    r=requests.get(f"{API}/products/search",headers=H,params={"site_id":"MLM","q":"JBL Go Essential 2 azul","status":"active","limit":10},timeout=15).json()
    for p in (r.get("results") or []):
        nm=(p.get("name") or "").lower()
        if "go essential" in nm and ("azul" in nm or "blue" in nm):
            azul_cpid=p["id"]
            azul_title=p.get("name") or azul_title
            print(f"  found via search: cpid={azul_cpid} name={azul_title}")
            break

TARGETS=[]
if azul_cpid:
    TARGETS.append(("AZUL",azul_cpid,azul_title))
TARGETS.append(("ROJO","MLM63638533","Parlante Portátil Bluetooth Jbl Go Essential 2 Rojo"))

# AH existing CPIDs (in Claribel)
own_cpids=set()
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,catalog_product_id"},timeout=20).json()
            for x in mg:
                if x.get("code")==200:
                    cp=(x["body"] or {}).get("catalog_product_id")
                    if cp: own_cpids.add(cp)
        if len(res)<50 or off>1000: break
        off+=50

# Category from existing JBL Go listings (we already have ELEC-013 etc.)
# Use MLM59800 which is the speakers category we used before
CAT="MLM59800"

published=[]
for color,cpid,title in TARGETS:
    print(f"\n=== Publishing {color} cpid={cpid} ===")
    if cpid in own_cpids:
        print(f"  ⚠ Claribel already has cpid {cpid}, skip")
        continue
    base={"site_id":"MLM","category_id":CAT,"price":549,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=40)
    if r.status_code not in (200,201):
        r=requests.post(f"{API}/items",headers=HJ,json={**base,"title":title},timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        published.append((color,cpid,d["id"],d.get("status"),d.get("price"),title))
        print(f"  ✓ PUBLISHED: {d['id']} {d.get('status')} ${d.get('price')}")
        print(f"    url={d.get('permalink')}")
    else:
        print(f"  ✗ FAIL {r.status_code}: {r.text[:400]}")
    time.sleep(1)

# Save to Supabase: no_replenish + strategy bounds
sb_url=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
sb_key=os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
if sb_key and published:
    print(f"\n=== Saving to Supabase ===")
    rows=[]
    for color,cpid,iid,st,pr,title in published:
        rows.append({"item_id":iid,"account":"Claribel","reason":"stock_limitado_1pza","product_name":title[:80]})
    try:
        r=requests.post(f"{sb_url}/rest/v1/meli_no_replenish_items",
            headers={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json","Prefer":"return=minimal,resolution=merge-duplicates"},
            json=rows,timeout=15)
        print(f"  no_replenish upsert: {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"  no_replenish exc: {e}")
else:
    print("\n⚠ No Supabase key — item_ids no se guardaron. Pasarlos a mano.")

print(f"\n=== RESUMEN ===")
print(f"published={len(published)}")
for color,cpid,iid,st,pr,title in published:
    print(f"  {color} cpid={cpid} new={iid} ${pr} {st}")
