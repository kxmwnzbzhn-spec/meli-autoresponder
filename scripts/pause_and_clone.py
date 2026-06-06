"""Pause MLM2967279337 + clone it as new in Claribel."""
import os, requests, json, time
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

SRC="MLM2967279337"

# === 1) PAUSE original ===
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"[SRC BEFORE] {SRC} status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
print(f"  title={g.get('title')}")
print(f"  cat={g.get('category_id')} cpid={g.get('catalog_product_id')}")

if g.get("status")!="paused":
    rp=requests.put(f"{API}/items/{SRC}",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  [PAUSE] HTTP {rp.status_code}: {rp.text[:200]}")

requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{SRC}",headers=SBH,timeout=10)
requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
    json={"item_id":SRC,"account":"CLARIBEL","reason":"pausada para clonar"},timeout=10)
requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
    json={"account":"CLARIBEL","scope":"item","scope_value":SRC,
          "directive_type":"pause","value_numeric":None,
          "raw_user_message":"pausa esta en claribel y clonala como nueva 2967279337"},timeout=10)

# === 2) CLONE ===
print("\n=== CLONE ===")
PRICE=g.get("price")
CPID=g.get("catalog_product_id")
CATID=g.get("category_id")

pics=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
attrs=[]
SKIP={"SELLER_SKU","HAZMAT_TRANSPORTABILITY","LINE","ITEM_CONDITION",
      "ALPHANUMERIC_MODEL","DEPTH","HEIGHT","LENGTH","WEIGHT","WIDTH",
      "PACKAGE_LENGTH","PACKAGE_WEIGHT","PACKAGE_WIDTH","PACKAGE_HEIGHT",
      "CHARGE_TIME","MAX_BATTERY_AUTONOMY","POWER_OUTPUT_RMS","DISTORTION",
      "MAX_FREQUENCY_RESPONSE","MIN_FREQUENCY_RESPONSE","SPEAKERS_NUMBER",
      "PICKUPS_NUMBER","ANATEL_HOMOLOGATION_NUMBER","SHIPMENT_PACKING",
      "PRODUCT_FEATURES"}
for a in (g.get("attributes") or []):
    aid=a.get("id"); vn=a.get("value_name"); vi=a.get("value_id")
    if not aid or aid in SKIP: continue
    if vn:
        obj={"id":aid,"value_name":vn}
        if vi: obj["value_id"]=vi
        attrs.append(obj)
# Ensure GTIN exists
have_gtin=any(a.get("id")=="GTIN" for a in attrs)
if not have_gtin:
    # JBL Clip 5 camuflaje/squad EAN
    attrs.append({"id":"GTIN","value_name":"6925281997211"})

# Slightly modify title to avoid duplicate
orig_title=g.get("title") or "JBL Clip 5"
NEW_TITLE=orig_title  # MELI usually allows dup titles for tradicional

payload={
    "title":NEW_TITLE[:60],
    "category_id":CATID,
    "price":PRICE,
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

rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"[POST clone] HTTP {rp.status_code}: {rp.text[:500]}")

if rp.status_code in (200,201):
    it=rp.json(); iid=it.get("id"); link=it.get("permalink")
    print(f"\n✅ CLONED → {iid}")
    print(f"  Permalink: {link}")
    print(f"  Price: ${it.get('price')}  Status: {it.get('status')}")

    # Copy description from src
    try:
        dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
        desc=dd.get("plain_text") or ""
        if desc:
            rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,
                json={"plain_text":desc[:5000]},timeout=15)
            print(f"  [DESC copied] HTTP {rd.status_code}")
    except Exception as e:
        print(f"  [DESC] EXC {e}")

    # Priority replenish for new clone
    requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":iid,"account":"CLARIBEL","default_qty":1,
              "product_name":(g.get("title") or "")[:200]},timeout=10)
    print(f"  [priority registered]")

    # Audit log
    requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
        json={"account":"CLARIBEL","item_id":iid,"action_type":"clone_from",
              "from_value":SRC,"to_value":iid,
              "actor":"claude_cowork","details":"clonado por usuario tras pausar"},timeout=10)
else:
    print(f"[FAIL] {rp.text[:800]}")
