"""Clone MLM2969870559 (Dior Sauvage Elixir) as tradicional in Adrián at $1999 with original brand."""
import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_AH={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

SRC="MLM2969870559"
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
pictures=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
print(f"[SRC] {SRC} title={g.get('title')}")
print(f"  pictures: {len(pictures)}")

# Get description
dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
src_desc=(dd.get("plain_text") or "")[:5000]

TITLE="Dior Sauvage Elixir Eau De Parfum 100ml"  # original title — 39 chars

# Datos originales del producto Dior Sauvage Elixir 100ml
# GTIN oficial EAN-13: 3348901577915
ATTRS=[
    {"id":"BRAND","value_name":"Dior"},
    {"id":"GTIN","value_name":"3348901577915"},
    {"id":"PERFUME_NAME","value_name":"Sauvage Elixir"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Sauvage Elixir"},
]

payload={
    "title":TITLE[:60],
    "category_id":"MLM1271",
    "price":1999,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":pictures,
    "attributes":ATTRS,
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
    ],
}

print("\n=== STEP 1: POST /items/validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
print(f"HTTP {rv.status_code}")
try:
    d=rv.json()
    causes=d.get("cause",[]) if isinstance(d,dict) else []
    real_errors=[c for c in causes if c.get("type")=="error"]
    print(f"  Real errors: {len(real_errors)}")
    for c in real_errors:
        print(f"    [{c.get('code')}] {c.get('message')}")
    if not real_errors: print("  ✅ Only warnings — safe to proceed")
except Exception as e: print(f"  json parse err {e}: {rv.text[:500]}")

proceed = rv.status_code in (200,204)
if not proceed:
    try:
        causes=rv.json().get("cause",[])
        has_real=any(c.get("type")=="error" for c in causes)
        if not has_real: proceed=True
    except: pass

if proceed:
    print("\n=== STEP 2: POST /items (real) ===")
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"HTTP {rp.status_code}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"\n✅ PUBLISHED {iid}")
        print(f"  Permalink: {link}")
        print(f"  Price: ${it.get('price')}  Status: {it.get('status')}")
        if src_desc:
            rd=requests.post(f"{API}/items/{iid}/description",headers=HJ,
                json={"plain_text":src_desc},timeout=15)
            print(f"  [DESC copied] HTTP {rd.status_code}")
        requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
            json={"account":"ADRIAN","item_id":iid,"action_type":"clone_dior_elixir",
                  "from_value":SRC,"to_value":f"{iid} brand=Dior price=1999",
                  "actor":"claude_cowork",
                  "details":"clone tradicional Dior Sauvage Elixir con brand original"},timeout=10)
        print("  [actions_log entry]")
    else:
        print(f"\n[POST FAILED] {rp.text[:1500]}")
else:
    print("\n[VALIDATE FAILED]")
    try:
        print(json.dumps(rv.json(), ensure_ascii=False, indent=2)[:2000])
    except: print(rv.text[:1500])
