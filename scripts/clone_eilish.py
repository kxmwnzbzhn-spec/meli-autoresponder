"""Publish Billie Eilish Eilish EDP 100ml as tradicional in Adrián at $1199."""
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

CPID="MLM47330605"
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
pictures=[{"source":pic.get("url")} for pic in (p.get("pictures") or []) if pic.get("url")]
print(f"[CATALOG] {p.get('name')} pics={len(pictures)}")
src_desc=(p.get("short_description") or {}).get("content","")[:5000] if p.get("short_description") else ""

TITLE="Billie Eilish Eilish Eau De Parfum 100ml"  # 40 chars

ATTRS=[
    {"id":"BRAND","value_name":"Billie Eilish"},
    {"id":"GTIN","value_name":"658925510412"},
    {"id":"PERFUME_NAME","value_name":"Eilish"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Eilish"},
]

payload={
    "title":TITLE[:60],
    "category_id":"MLM1271",
    "price":1199,
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
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"POST HTTP {rp.status_code}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"✅ {iid} ${it.get('price')} | {link}")
        if src_desc:
            requests.post(f"{API}/items/{iid}/description",headers=HJ,
                json={"plain_text":src_desc},timeout=15)
            print(f"  [DESC catalog]")
        requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
            json={"account":"ADRIAN","item_id":iid,"action_type":"clone_eilish",
                  "from_value":CPID,"to_value":f"{iid} brand=BillieEilish price=1199",
                  "actor":"claude_cowork","details":"clone Billie Eilish Eilish EDP 100ml"},timeout=10)
    else:
        print(f"[POST FAILED] {rp.text[:1500]}")
else:
    print(f"[VALIDATE FAILED]")
    try: print(json.dumps(rv.json(), ensure_ascii=False, indent=2)[:2000])
    except: print(rv.text[:1500])
