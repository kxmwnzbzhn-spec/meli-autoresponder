"""Generic single-item pin with full Supabase tracking + price set."""
import os, requests
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

ITEM=os.environ["TARGET_ITEM"]
ACCOUNT=os.environ["TARGET_ACCOUNT"].upper()
PRICE=float(os.environ["TARGET_PRICE"])
USER_MSG=os.environ.get("RAW_MSG", f"pin {ITEM} a ${PRICE}")
SECRET="MELI_REFRESH_TOKEN_"+ACCOUNT

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ[SECRET]},timeout=20).json()
AT=r["access_token"]
print(f"NEW_RT_{ACCOUNT}={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=15).json()
cur=g.get("price"); cpid=g.get("catalog_product_id"); st=g.get("status"); sub=g.get("sub_status")
sku_attr=[a for a in (g.get("attributes") or []) if a.get("id")=="SELLER_SKU"]
sku=(sku_attr[0].get("value_name") if sku_attr else None) or g.get("seller_custom_field")
print(f"[ITEM] {ITEM} status={st} sub={sub} | price={cur} → {PRICE} | sku={sku} cpid={cpid}")
print(f"  title={g.get('title')}")

# 1) Directive: pin_price
d={"account":ACCOUNT,"scope":"item","scope_value":ITEM,
   "directive_type":"pin_price","value_numeric":PRICE,"raw_user_message":USER_MSG}
rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,json=d,timeout=15)
print(f"[DIRECTIVE pin_price] HTTP {rd.status_code}: {rd.text[:200]}")

# 2) Strategy: floor=ceiling=PRICE if CPID exists
if cpid:
    body={"floor":PRICE,"ceiling":PRICE}
    ru=requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}",
                     headers=SBH,json=body,timeout=15)
    print(f"[STRAT PATCH cpid={cpid}] HTTP {ru.status_code}: {ru.text[:200]}")
    if ru.status_code in (200,201,204) and ru.text in ("","[]"):
        # No row existed, upsert
        up={"sku":sku or "UNKNOWN","catalog_product_id":cpid,"floor":PRICE,"ceiling":PRICE,"account":ACCOUNT}
        ru2=requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
            headers={**SBH,"Prefer":"return=representation,resolution=merge-duplicates"},
            json=up,timeout=15)
        print(f"[STRAT UPSERT] HTTP {ru2.status_code}: {ru2.text[:200]}")
else:
    print("[WARN] no cpid — strategy update no aplica")

# 3) PUT precio + activar
payload={"price":PRICE}
if st!="active":
    payload["status"]="active"
rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=15)
print(f"[PRICE SET {cur}→{PRICE}] HTTP {rr.status_code}: {rr.text[:300]}")

# 4) audit log
log={"account":ACCOUNT,"item_id":ITEM,"action_type":"price_set",
     "from_value":str(cur),"to_value":str(PRICE),
     "actor":"claude_cowork","details":USER_MSG}
rl=requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,json=log,timeout=15)
print(f"[ACTLOG] HTTP {rl.status_code}")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[VERIFY] price={g2.get('price')} status={g2.get('status')}")
