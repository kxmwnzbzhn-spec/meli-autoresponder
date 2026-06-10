"""Batch clone 5 perfumes tradicional in Adrián with original brand data."""
import os, requests, json, time
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

# [src_id, title, price, BRAND, PERFUME_NAME, PERFUME_TYPE, UNIT_VOLUME, GENDER, MODEL, GTIN]
JOBS=[
    ("MLM2969839267", "Al Haramain Amber Oud Private Edition Unisex 60ml EDP", 1499,
     "Al Haramain","Amber Oud Private Edition","Eau de parfum","60 mL","Sin género","Amber Oud Private Edition","6291100137664"),
    ("MLM2969839197", "Armani Stronger With You Tobacco EDP 100ml Hombre", 1499,
     "Armani Beauty","Stronger With You Tobacco","Eau de parfum","100 mL","Hombre","Stronger With You Tobacco","3614272476769"),
    ("MLM2969839167", "Armani Code Le Parfum 125ml Hombre", 1199,
     "Armani","Code","Parfum","125 mL","Hombre","Code Le Parfum","3614274073645"),
    ("MLM2969825393", "Armaf Club De Nuit Iconic EDP 105ml Hombre", 1199,
     "Armaf","Club De Nuit Iconic","Eau de parfum","105 mL","Hombre","Club De Nuit Iconic","6294015164497"),
    ("MLM2969851519", "Giorgio Armani My Way Eau De Parfum 90ml Mujer", 1499,
     "Armani","My Way","Eau de parfum","90 mL","Mujer","My Way","3614272909083"),
]

results=[]
for (SRC, TITLE, PRICE, BRAND, PERFUME_NAME, PERFUME_TYPE, UNIT_VOLUME, GENDER, MODEL, GTIN) in JOBS:
    print(f"\n========== {SRC} → {TITLE[:50]} (${PRICE}) ==========")
    try:
        g=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
        pictures=[{"source":p.get("url")} for p in (g.get("pictures") or []) if p.get("url")]
        dd=requests.get(f"{API}/items/{SRC}/description",headers=H,timeout=10).json()
        src_desc=(dd.get("plain_text") or "")[:5000]
        
        ATTRS=[
            {"id":"BRAND","value_name":BRAND},
            {"id":"GTIN","value_name":GTIN},
            {"id":"PERFUME_NAME","value_name":PERFUME_NAME},
            {"id":"PERFUME_TYPE","value_name":PERFUME_TYPE},
            {"id":"UNIT_VOLUME","value_name":UNIT_VOLUME},
            {"id":"GENDER","value_name":GENDER},
            {"id":"ITEM_CONDITION","value_name":"Nuevo"},
            {"id":"MODEL","value_name":MODEL},
        ]
        payload={
            "title":TITLE[:60],
            "category_id":"MLM1271",
            "price":PRICE,
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
        
        # Validate
        rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
        causes=rv.json().get("cause",[]) if rv.status_code==400 else []
        real_errors=[c for c in causes if c.get("type")=="error"]
        if real_errors and rv.status_code not in (200,204):
            print(f"  ❌ VALIDATE errors:")
            for c in real_errors:
                print(f"    [{c.get('code')}] {c.get('message')[:140]}")
            results.append((SRC,"validate_failed",None))
            continue
        
        # POST
        rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
        if rp.status_code in (200,201):
            it=rp.json(); iid=it.get("id"); link=it.get("permalink")
            print(f"  ✅ {iid} ${it.get('price')} | {link}")
            if src_desc:
                requests.post(f"{API}/items/{iid}/description",headers=HJ,
                    json={"plain_text":src_desc},timeout=15)
            requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
                json={"account":"ADRIAN","item_id":iid,"action_type":"clone_with_brand",
                      "from_value":SRC,"to_value":f"{iid} brand={BRAND} price={PRICE}",
                      "actor":"claude_cowork","details":f"clone tradicional {BRAND} {PERFUME_NAME}"},timeout=10)
            results.append((SRC,"ok",iid))
        else:
            print(f"  ❌ POST failed HTTP {rp.status_code}: {rp.text[:300]}")
            results.append((SRC,"post_failed",None))
    except Exception as e:
        print(f"  EXC {e}")
        results.append((SRC,"exc",str(e)))
    time.sleep(0.5)

print(f"\n=== FINAL ===")
for src,status,new in results:
    print(f"  {src}: {status} → {new}")
