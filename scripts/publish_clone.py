"""Clone an existing Claribel JBL Go 4 listing, swap to Celeste color + pictures."""
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

SRC="MLM2967317601"  # existing Claribel Go 4 Rojo
CPID_CELESTE="MLM61262890"
FLOOR=499; CEIL=549; PRICE=549

g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"[SRC] {SRC} title={g.get('title')} cat={g.get('category_id')} status={g.get('status')}")

# Get Celeste catalog product for pictures
pc=requests.get(f"{API}/products/{CPID_CELESTE}",headers=H,timeout=10).json()
celeste_pics=[{"source":p.get("url")} for p in (pc.get("pictures") or []) if p.get("url")]
print(f"  Celeste catalog has {len(celeste_pics)} pictures")

# Build payload from SRC, swap color
attrs=[]
for a in (g.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    if not aid: continue
    if aid in ("SELLER_SKU","GTIN"): continue
    if aid in ("COLOR","MAIN_COLOR"):
        attrs.append({"id":aid,"value_name":"Celeste"})
        continue
    if vn:
        obj={"id":aid,"value_name":vn}
        if vi: obj["value_id"]=vi
        attrs.append(obj)
# Add EMPTY_GTIN_REASON if SRC didn't have GTIN
have_gtin=any(a.get("id")=="GTIN" for a in attrs)
have_egr=any(a.get("id")=="EMPTY_GTIN_REASON" for a in attrs)
if not have_gtin and not have_egr:
    attrs.append({"id":"GTIN","value_name":"6925281996528"})

TITLE="Bocina JBL Go 4 Celeste Bluetooth Waterproof Portátil"[:60]
payload={
    "title":TITLE,
    "category_id":g.get("category_id"),
    "price":PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":celeste_pics,
    "attributes":attrs,
    "shipping":g.get("shipping") or {"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":g.get("sale_terms") or [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ PUBLISHED {iid}")
    print(f"  Permalink: {link}")
    print(f"  Price: ${it.get('price')}")
    
    # Set description
    DESC=("JBL Go 4 Celeste - Bocina Bluetooth portátil impermeable. "
          "Sonido potente JBL Pro Sound en formato ultraportátil. "
          "Hasta 7 horas de batería. Resistente al agua y al polvo IP67. "
          "Estuche flotante incluido. Color Celeste original JBL.")
    rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
    print(f"  [DESC] HTTP {rd.status_code}")

    # Supabase
    for dt,val in [("set_floor",FLOOR),("set_ceiling",CEIL)]:
        for scope,sv in [("item",iid),("cpid",CPID_CELESTE)]:
            requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"CLARIBEL","scope":scope,"scope_value":sv,
                      "directive_type":dt,"value_numeric":val,
                      "raw_user_message":"publicame catalogo claribel min 499 max 549 MLM61262890"},timeout=10)
    # strategy
    ru=requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{CPID_CELESTE}",
        headers={**SBH,"Prefer":"return=representation"},
        json={"floor":FLOOR,"ceiling":CEIL,"active":True},timeout=10)
    print(f"  [STRAT PATCH] HTTP {ru.status_code}: {ru.text[:160]}")
    if ru.status_code==200 and ru.text in ("","[]"):
        requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
            headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
            json={"sku":"JBL-GO4-CELESTE","catalog_product_id":CPID_CELESTE,
                  "floor":FLOOR,"ceiling":CEIL,"active":True,"priority":1,
                  "source":"user_publish_2026-06-05","notes":"Claribel Celeste clone"},timeout=10)
        print(f"  [STRAT UPSERT done]")
    # Priority
    requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":iid,"account":"CLARIBEL","default_qty":1,
              "product_name":"JBL Go 4 Celeste"},timeout=10)
    print(f"  [priority added]")
