"""Batch: close MLM5241635216 + set_floor 699 on MLM5244434176 (Claribel)."""
import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# === A) CLOSE MLM5241635216 ===
ITEM_A="MLM5241635216"
USER_MSG_A="esta tambien 5241635216 (cerrar)"
print(f"\n========== CLOSE {ITEM_A} ==========")
g=requests.get(f"{API}/items/{ITEM_A}",headers=H,timeout=10).json()
print(f"[BEFORE] status={g.get('status')} sub={g.get('sub_status')} price={g.get('price')} title={(g.get('title') or '')[:80]}")
if g.get("status")=="active":
    rp=requests.put(f"{API}/items/{ITEM_A}",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  [PAUSE] HTTP {rp.status_code}")
rc=requests.put(f"{API}/items/{ITEM_A}",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  [CLOSE] HTTP {rc.status_code}: {rc.text[:200]}")
if SBH:
    requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{ITEM_A}",headers=SBH,timeout=10)
    requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":ITEM_A,"account":"CLARIBEL","reason":"cerrado por usuario"},timeout=10)
    requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"CLARIBEL","scope":"item","scope_value":ITEM_A,
              "directive_type":"close","value_numeric":None,"raw_user_message":USER_MSG_A},timeout=10)
g2=requests.get(f"{API}/items/{ITEM_A}",headers=H,timeout=10).json()
print(f"[AFTER] status={g2.get('status')} sub={g2.get('sub_status')}")

# === B) FLOOR=699 on MLM5244434176 ===
ITEM_B="MLM5244434176"
USER_MSG_B="a esta ponle un precio limite de piso 5244434176 de $699"
FLOOR=699.0
print(f"\n========== SET FLOOR ${FLOOR} on {ITEM_B} ==========")
g=requests.get(f"{API}/items/{ITEM_B}",headers=H,timeout=10).json()
cur=g.get("price"); cpid=g.get("catalog_product_id")
sku_attr=[a for a in (g.get("attributes") or []) if a.get("id")=="SELLER_SKU"]
sku=(sku_attr[0].get("value_name") if sku_attr else None) or g.get("seller_custom_field")
print(f"[BEFORE] status={g.get('status')} sub={g.get('sub_status')} | price={cur} | sku={sku} cpid={cpid}")
print(f"  title={(g.get('title') or '')[:80]}")

# Directive set_floor
if SBH:
    rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"CLARIBEL","scope":"item","scope_value":ITEM_B,
              "directive_type":"set_floor","value_numeric":FLOOR,"raw_user_message":USER_MSG_B},timeout=10)
    print(f"  [DIR set_floor item] HTTP {rd.status_code}")
    if cpid:
        rd2=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
            json={"account":"CLARIBEL","scope":"cpid","scope_value":cpid,
                  "directive_type":"set_floor","value_numeric":FLOOR,"raw_user_message":USER_MSG_B},timeout=10)
        print(f"  [DIR set_floor cpid] HTTP {rd2.status_code}")
        ru=requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}",
            headers={**SBH,"Prefer":"return=representation"},json={"floor":FLOOR},timeout=10)
        print(f"  [STRAT PATCH floor cpid={cpid}] HTTP {ru.status_code}: {ru.text[:200]}")
        if ru.status_code in (200,204) and ru.text in ("","[]"):
            up={"sku":sku or "UNKNOWN","catalog_product_id":cpid,"floor":FLOOR,"ceiling":999999,"account":"CLARIBEL"}
            ru2=requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=representation"},
                json=up,timeout=10)
            print(f"  [STRAT UPSERT] HTTP {ru2.status_code}: {ru2.text[:200]}")

# Force price up if below floor
if cur is not None and float(cur)<FLOOR:
    rr=requests.put(f"{API}/items/{ITEM_B}",headers=HJ,json={"price":FLOOR},timeout=15)
    print(f"  [PRICE {cur}→{FLOOR}] HTTP {rr.status_code}: {rr.text[:200]}")
else:
    print(f"  [PRICE OK] {cur} >= floor {FLOOR}")

# Activate if paused
if g.get("status")!="active":
    ra=requests.put(f"{API}/items/{ITEM_B}",headers=HJ,json={"status":"active"},timeout=15)
    print(f"  [ACTIVATE] HTTP {ra.status_code}")

g3=requests.get(f"{API}/items/{ITEM_B}",headers=H,timeout=10).json()
print(f"[AFTER] status={g3.get('status')} price={g3.get('price')}")
