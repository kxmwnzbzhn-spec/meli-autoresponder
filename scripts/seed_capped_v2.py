"""Seed capped table + set MELI qty=1 active on the 2 items."""
import os, requests
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

ITEMS=[
    {"item_id":"MLM2967279139","account":"CLARIBEL","visible_qty":1,"remaining":89,"original":89,
     "notes":"JBL Go 3 Negro - capped 89 piezas, pausa al 0"},
    {"item_id":"MLM2967317601","account":"CLARIBEL","visible_qty":1,"remaining":19,"original":19,
     "notes":"JBL Go 4 Rojo - capped 19 piezas, pausa al 0"},
]

# 1) Upsert
ru=requests.post(f"{SBU}/rest/v1/meli_stock_capped",
    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=representation"},
    json=ITEMS,timeout=15)
print(f"\n[SUPABASE UPSERT] HTTP {ru.status_code}: {ru.text[:500]}")

# 2) Also add to meli_priority_replenish so bot picks them up
for it in ITEMS:
    rp=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":it["item_id"],"account":it["account"],"default_qty":it["visible_qty"],
              "product_name":it["notes"]},timeout=10)
    print(f"  [priority {it['item_id']}] HTTP {rp.status_code}")
    # Remove from no_replenish if present (was paused earlier)
    requests.delete(f"{SBU}/rest/v1/meli_no_replenish_items?item_id=eq.{it['item_id']}",headers=SBH,timeout=10)
    # Directive
    requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
        json={"account":it["account"],"scope":"item","scope_value":it["item_id"],
              "directive_type":"stock_capped","value_numeric":it["remaining"],
              "raw_user_message":f"A esta {it['item_id']} stock real {it['remaining']} a la vista {it['visible_qty']}, cuando se acabe pausar"},timeout=10)

# 3) Set MELI qty=1 active on each
for it in ITEMS:
    g=requests.get(f"{API}/items/{it['item_id']}",headers=H,timeout=10).json()
    print(f"\n{it['item_id']} BEFORE status={g.get('status')} qty={g.get('available_quantity')} title={(g.get('title') or '')[:80]}")
    rr=requests.put(f"{API}/items/{it['item_id']}",headers=HJ,
        json={"status":"active","available_quantity":it["visible_qty"]},timeout=15)
    print(f"  PUT status=active qty={it['visible_qty']} → HTTP {rr.status_code}: {rr.text[:200]}")

# 4) Show capped table state
rv=requests.get(f"{SBU}/rest/v1/meli_stock_capped?account=eq.CLARIBEL&select=*",headers=SBH,timeout=10)
print(f"\n=== meli_stock_capped (CLARIBEL) ===\n{rv.text}")
