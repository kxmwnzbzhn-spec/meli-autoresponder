import os, requests, sys, json, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

# DIRECTIVAS:
# A) MLM2967318097 ceiling=1499 (floor sin cambio o 1)
# B) [2967318191, 2967317601, 2967305251, 2967317613, 2967292003] floor=499 ceiling=549

JOBS=[
  {"item":"MLM2967318097","floor":None,"ceiling":1499,
   "raw":"pon esta precio maximo 1499 2967318097",
   "dt":"set_ceiling"},
]
for x in ["2967318191","2967317601","2967305251","2967317613","2967292003"]:
    JOBS.append({"item":f"MLM{x}","floor":499,"ceiling":549,
                 "raw":"estas en 549: 2967318191,2967317601,2967305251,2967317613,2967292003, ese es el precio mas alto y el minimo es el $499",
                 "dt":"pin_band"})
# C) ceiling=799 (floor flexible)
for x in ["2967292013","2967279337","2967292049","2967292015"]:
    JOBS.append({"item":f"MLM{x}","floor":None,"ceiling":799,
                 "raw":"estas ponlas precio maximo 799: 2967292013,2967279337,2967292049,2967292015",
                 "dt":"set_ceiling"})

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; NEW_RT=r.get("refresh_token")
print("[OAUTH] ok rt_len=",len(NEW_RT or ""))
H={"Authorization":f"Bearer {AT}"}
HJ={**H,"Content-Type":"application/json"}

def patch_strategy(cpid,sku,floor,ceil):
    body={}
    if floor is not None: body["floor"]=floor
    if ceil  is not None: body["ceiling"]=ceil
    if not body: return
    ru=requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}",
                      headers=SBH,json=body,timeout=15)
    print(f"  [STRAT PATCH cpid={cpid}]",ru.status_code,ru.text[:150])
    if ru.status_code in (200,201,204) and ru.text not in ("","[]"):
        return True
    # Upsert
    up={"sku":sku or "UNKNOWN","catalog_product_id":cpid,
        "floor":floor if floor is not None else 1,
        "ceiling":ceil if ceil is not None else 999999,
        "account":"CLARIBEL"}
    ru2=requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
        headers={**SBH,"Prefer":"return=representation,resolution=merge-duplicates"},
        json=up,timeout=15)
    print(f"  [STRAT UPSERT cpid={cpid}]",ru2.status_code,ru2.text[:150])

for j in JOBS:
    iid=j["item"]; floor=j["floor"]; ceil=j["ceiling"]
    print(f"\n=== {iid} floor={floor} ceiling={ceil} ===")
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    except Exception as e:
        print(f"  [GET ERR]",e); continue
    sku_attr=[a for a in (g.get("attributes") or []) if a.get("id")=="SELLER_SKU"]
    sku=(sku_attr[0].get("value_name") if sku_attr else None) or g.get("seller_custom_field")
    cpid=g.get("catalog_product_id")
    cur=g.get("price"); st=g.get("status"); sub=g.get("sub_status"); title=g.get("title")
    print(f"  status={st} sub={sub} price={cur} sku={sku} cpid={cpid}")
    print(f"  title={title}")

    # 1) directive
    d={"account":"CLARIBEL","scope":"item","scope_value":iid,
       "directive_type":j["dt"],
       "value_numeric":ceil if ceil is not None else floor,
       "raw_user_message":j["raw"]}
    rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,json=d,timeout=15)
    print(f"  [DIRECTIVE]",rd.status_code,rd.text[:120])

    # also write set_floor directive if both
    if floor is not None and ceil is not None:
        d2={"account":"CLARIBEL","scope":"item","scope_value":iid,
            "directive_type":"set_floor","value_numeric":floor,
            "raw_user_message":j["raw"]}
        rd2=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,json=d2,timeout=15)
        print(f"  [DIRECTIVE floor]",rd2.status_code,rd2.text[:120])

    # 2) strategy
    if cpid:
        patch_strategy(cpid,sku,floor,ceil)
    else:
        print("  [WARN] no cpid -> strategy update por item_id no aplica directamente")

    # 3) precio: forzar a ceiling si fuera de banda
    target=None
    if cur is not None:
        cv=float(cur)
        if ceil is not None and cv>ceil:   target=ceil
        elif floor is not None and cv<floor: target=floor
    if target is not None and target!=cur:
        pr=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
        print(f"  [PRICE {cur}->{target}]",pr.status_code,pr.text[:200])
        log={"account":"CLARIBEL","item_id":iid,"action_type":"price_set",
             "from_value":str(cur),"to_value":str(target),
             "actor":"claude_cowork","details":j["raw"]}
        requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,json=log,timeout=15)
    else:
        print(f"  [PRICE OK] {cur} in band [{floor},{ceil}]")

    # 4) activar si no activo
    if st!="active":
        ra=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"  [ACTIVATE]",ra.status_code,ra.text[:200])

    # 5) actions_log marker
    log2={"account":"CLARIBEL","item_id":iid,"action_type":j["dt"],
          "from_value":f"floor=?, ceiling=?",
          "to_value":f"floor={floor}, ceiling={ceil}",
          "actor":"claude_cowork","details":j["raw"]}
    requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,json=log2,timeout=15)

print("\n[DONE ALL]")
