"""Set qty=1 per variation on MLM2976325463 + register variation-level auto-replenish."""
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

ITEM="MLM2976325463"
USER_MSG="ponle reauto stock a esto cada que se venda una pieza se agrega 1 mas en automatico ponle 1 pieza a cada variante 2976325463"

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=15).json()
print(f"[BEFORE] {ITEM} status={g.get('status')} item_qty={g.get('available_quantity')} variations={len(g.get('variations') or [])}")
for v in (g.get("variations") or []):
    combo=v.get("attribute_combinations") or []
    ac_str={a.get("id"):a.get("value_name") for a in combo}
    print(f"  variation_id={v.get('id')} {ac_str} qty={v.get('available_quantity')} price={v.get('price')}")

# Build variations payload: each with qty=1
new_vars=[]
for v in (g.get("variations") or []):
    new_vars.append({
        "id":v.get("id"),
        "available_quantity":1,
    })

print(f"\n=== PUT variations qty=1 each + status=active ===")
payload={"status":"active","variations":new_vars}
rr=requests.put(f"{API}/items/{ITEM}",headers=HJ,json=payload,timeout=20)
print(f"HTTP {rr.status_code}: {rr.text[:600]}")

if rr.status_code in (200,201):
    g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
    print(f"\n[AFTER] status={g2.get('status')} qty={g2.get('available_quantity')}")
    for v in (g2.get("variations") or []):
        combo=v.get("attribute_combinations") or []
        ac_str={a.get("id"):a.get("value_name") for a in combo}
        print(f"  variation_id={v.get('id')} {ac_str} qty={v.get('available_quantity')}")
    print(f"Permalink: {g2.get('permalink')}")
    
    # Register in priority_replenish — total qty should be 3 (1 per variant × 3)
    total_qty=sum((v.get("available_quantity") or 0) for v in (g2.get("variations") or []))
    print(f"  total qty across variants = {total_qty}")
    
    requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":ITEM,"account":"ADRIAN","default_qty":total_qty,
              "product_name":g2.get("title","")[:200]},timeout=10)
    # Remove from no_replenish if present
    requests.delete(f"{SBU}/rest/v1/meli_no_replenish_items?item_id=eq.{ITEM}",headers=SBH,timeout=8)
    requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":"ADRIAN","scope":"item","scope_value":ITEM,
              "directive_type":"priority_replenish","value_numeric":total_qty,
              "raw_user_message":USER_MSG},timeout=10)
    # Also write a variation-aware capped row to flag the bot
    requests.post(f"{SBU}/rest/v1/meli_stock_capped",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":ITEM,"account":"ADRIAN","visible_qty":total_qty,
              "remaining":999999,"original":999999,"auto_pause_when_zero":False,
              "notes":f"CK Boxer 3 variantes 1 c/u - replenish infinito (cada venta repone 1)"},timeout=10)
    print(f"  [priority + capped registered]")
else:
    print(f"[FAIL] {rr.text[:1000]}")
