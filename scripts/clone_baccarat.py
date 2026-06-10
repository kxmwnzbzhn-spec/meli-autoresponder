"""Clone MLM2969870649 (Baccarat Rouge 540 Extrait MFK 70ml) tradicional in Adrián at $1999."""
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

SRC="MLM2969870649"
g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
pictures=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
print(f"[SRC] title={g.get('title')} pics={len(pictures)}")
dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
src_desc=(dd.get("plain_text") or "")[:5000]

TITLE="Maison Francis Kurkdjian Baccarat Rouge 540 Extrait 70ml"  # 56 chars

ATTRS=[
    {"id":"BRAND","value_name":"Maison Francis Kurkdjian"},
    {"id":"GTIN","value_name":"3700559606810"},
    {"id":"PERFUME_NAME","value_name":"Baccarat Rouge 540 Extrait"},
    {"id":"PERFUME_TYPE","value_name":"Parfum"},
    {"id":"UNIT_VOLUME","value_name":"70 mL"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Baccarat Rouge 540 Extrait"},
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

print("\n=== Validate ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
real_errors=[]
try:
    causes=rv.json().get("cause",[])
    real_errors=[c for c in causes if c.get("type")=="error"]
    for c in real_errors:
        print(f"  ❌ [{c.get('code')}] {c.get('message')[:180]}")
except: pass
proceed = rv.status_code in (200,204) or not real_errors

if proceed:
    print("\n=== POST /items ===")
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"HTTP {rp.status_code}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"✅ {iid} ${it.get('price')} | {link}")
        if src_desc:
            requests.post(f"{API}/items/{iid}/description",headers=HJ,
                json={"plain_text":src_desc},timeout=15)
            print(f"  [DESC copied]")
        requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
            json={"account":"ADRIAN","item_id":iid,"action_type":"clone_baccarat",
                  "from_value":SRC,"to_value":f"{iid} brand=MFK price=1999",
                  "actor":"claude_cowork","details":"clone MFK Baccarat Rouge 540 Extrait"},timeout=10)
    else:
        print(f"[POST FAILED] {rp.text[:1500]}")
else:
    print("\n[VALIDATE FAILED]")
    try: print(json.dumps(rv.json(), ensure_ascii=False, indent=2)[:2000])
    except: print(rv.text[:1500])
