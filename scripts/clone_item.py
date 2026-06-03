"""Clone MLM5233454100 since it's closed with has_bids=true and cannot be revived."""
import os, requests, json, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

SRC="MLM5233454100"
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"[SRC] title={g.get('title')}")
print(f"  cat={g.get('category_id')} price={g.get('price')} qty_avail={g.get('available_quantity')} sold={g.get('sold_quantity')}")

# Get description
dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
desc=(dd.get("plain_text") or "")[:5000]
print(f"  description={len(desc)} chars")

# Build clone payload
pictures=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
attrs=[]
for a in (g.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    if not aid: continue
    # Skip system-set attrs that shouldn't be re-posted
    if aid in ("GTIN",): continue
    obj={"id":aid}
    if vi: obj["value_id"]=vi
    elif vn: obj["value_name"]=vn
    if vn or vi: attrs.append(obj)

payload={
    "title":g.get("title"),
    "category_id":g.get("category_id"),
    "price":g.get("price") or 199,
    "currency_id":g.get("currency_id") or "MXN",
    "available_quantity":1,  # start with 1 — bot will manage replenish
    "buying_mode":"buy_it_now",
    "condition":g.get("condition") or "new",
    "listing_type_id":"gold_special",
    "pictures":pictures,
    "attributes":attrs,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":g.get("sale_terms") or [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST /items (clone) ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ CLONED → {iid}")
    print(f"Permalink: {link}")
    # Set description
    if desc:
        rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=15)
        print(f"[DESC] HTTP {rd.status_code}: {rd.text[:200]}")
    # Register in priority_replenish so it auto-revives on sales
    if SBK:
        SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
        rr=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",headers=SBH,
            json={"item_id":iid,"account":"ASVA","default_qty":1,"product_name":g.get("title","")[:200]},
            timeout=10)
        print(f"[PRIORITY] HTTP {rr.status_code}")
