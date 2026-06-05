"""Publish MLM61262890 catalog in Claribel + register bounds [499,549]."""
import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

CPID="MLM61262890"
FLOOR=499; CEIL=549; PRICE=549

# Confirm catalog product accepts publish
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=10).json()
print(f"\n[CATALOG] {CPID} name={p.get('name')} status={p.get('status')} pdp_types={p.get('pdp_types')}")

# pdp_types=traditional means we can't use catalog_listing=true; publish as tradicional with CPID reference
title = p.get("name") or "Bocina JBL Go 4 Celeste Bluetooth Waterproof"
category_id = p.get("category_id") or "MLM59800"
pictures = [{"source":pic.get("url")} for pic in (p.get("pictures") or []) if pic.get("url")]
# Extract attributes from catalog (BRAND, MODEL, COLOR etc.)
attrs=[]
for a in (p.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    if not aid: continue
    if aid in ("GTIN","SELLER_SKU"): continue
    if vi: attrs.append({"id":aid,"value_id":vi})
    elif vn: attrs.append({"id":aid,"value_name":vn})

payload={
    "title":title[:60],
    "category_id":category_id,
    "catalog_product_id":CPID,
    "price":PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":pictures,
    "attributes":attrs,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items/validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
print(f"HTTP {rv.status_code}: {rv.text[:1500]}")

print("\n=== POST /items (real) ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"  Permalink: {link}")
    print(f"  Price: ${it.get('price')}")

    # Supabase: directives + strategy + priority + sku_map
    for dt,val,msg in [("set_floor",FLOOR,f"floor {FLOOR}"),("set_ceiling",CEIL,f"ceiling {CEIL}")]:
        for scope,scope_val in [("item",iid),("cpid",CPID)]:
            rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"CLARIBEL","scope":scope,"scope_value":scope_val,
                      "directive_type":dt,"value_numeric":val,
                      "raw_user_message":f"publicame esta en catalogo claribel min 499 max 549 MLM61262890"},timeout=10)
            print(f"  [DIR {dt} {scope}={scope_val}] HTTP {rd.status_code}")
    
    # Strategy
    ru=requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{CPID}",
        headers={**SBH,"Prefer":"return=representation"},
        json={"floor":FLOOR,"ceiling":CEIL,"active":True},timeout=15)
    print(f"  [STRAT PATCH] HTTP {ru.status_code}: {ru.text[:200]}")
    if ru.status_code==200 and ru.text in ("","[]"):
        ru2=requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
            headers={**SBH,"Prefer":"resolution=merge-duplicates,return=representation"},
            json={"sku":"JBL-GO4-CELESTE","catalog_product_id":CPID,
                  "floor":FLOOR,"ceiling":CEIL,"active":True,"priority":1,
                  "source":"user_publish_2026-06-05","notes":"Claribel publish Celeste"},timeout=10)
        print(f"  [STRAT UPSERT] HTTP {ru2.status_code}: {ru2.text[:200]}")

    # Priority replenish for war/auto-replenish
    rpr=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":iid,"account":"CLARIBEL","default_qty":1,
              "product_name":"JBL Go 4 Celeste"},timeout=10)
    print(f"  [priority] HTTP {rpr.status_code}")

    # Actions log
    rl=requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
        json={"account":"CLARIBEL","item_id":iid,"action_type":"publish_catalog",
              "from_value":"none","to_value":f"cpid={CPID} price={PRICE} bounds=[{FLOOR},{CEIL}]",
              "actor":"claude_cowork",
              "details":"JBL Go 4 Celeste catalog publish con bounds"},timeout=10)
    print(f"  [ACTLOG] HTTP {rl.status_code}")
else:
    print(f"\n[FAIL] no se publicó: {rp.text[:1500]}")
