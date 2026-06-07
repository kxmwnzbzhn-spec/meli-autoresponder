"""The original CK boxer MLM2976325463 is locked (has_bids+qty=0). Clone it fresh."""
import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

SRC="MLM2976325463"
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"[SRC] {SRC} status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
print(f"  title={g.get('title')}")

pics=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
attrs=[]
SKIP={"SELLER_SKU","HAZMAT_TRANSPORTABILITY","LINE","ITEM_CONDITION",
      "ALPHANUMERIC_MODEL","DEPTH","HEIGHT","LENGTH","WEIGHT","WIDTH",
      "PACKAGE_LENGTH","PACKAGE_WEIGHT","PACKAGE_WIDTH","PACKAGE_HEIGHT",
      "SHIPMENT_PACKING","PRODUCT_FEATURES"}
for a in (g.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    if not aid or aid in SKIP: continue
    if vn:
        obj={"id":aid,"value_name":vn}
        if vi: obj["value_id"]=vi
        attrs.append(obj)

payload={
    "title":(g.get("title") or "Calvin Klein Pack 3 Boxers")[:60],
    "category_id":g.get("category_id"),
    "price":g.get("price") or 799,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":g.get("condition") or "new",
    "listing_type_id":"gold_special",
    "pictures":pics,
    "attributes":attrs,
    "shipping":g.get("shipping") or {"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":g.get("sale_terms") or [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== POST clone ===")
rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"HTTP {rp.status_code}: {rp.text[:1500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ CLONED → {iid}")
    print(f"  Permalink: {link}")
    # Copy description
    try:
        dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
        desc=dd.get("plain_text") or ""
        if desc:
            rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,
                json={"plain_text":desc[:5000]},timeout=15)
            print(f"  [DESC copied] HTTP {rd.status_code}")
    except: pass
    # Audit log
    requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
        json={"account":"ADRIAN","item_id":iid,"action_type":"clone_from",
              "from_value":SRC,"to_value":iid,
              "actor":"claude_cowork",
              "details":"clonado porque src tiene has_bids=true y qty locked"},timeout=10)
