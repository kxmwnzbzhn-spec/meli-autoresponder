import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

ITEM="MLM3849137034"

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; NEW_RT=r.get("refresh_token")
print(f"NEW_RT_ASVA={NEW_RT}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=15).json()
inv=g.get("inventory_id"); upid=g.get("user_product_id"); qty=g.get("available_quantity"); st=g.get("status")
title=g.get("title")
print(f"[ITEM] status={st} qty={qty} inv={inv} upid={upid}")
print(f"  title={title}")

# Try qty=1
print("\n[TRY] PUT available_quantity=1 directly on item:")
r1=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"available_quantity":1},timeout=15)
print(f"  HTTP {r1.status_code}: {r1.text[:400]}")

# If failed and there's inventory_id (FBM), try inventory endpoint
if r1.status_code not in (200,201) and inv:
    print(f"\n[TRY] direct item PUT rechazo. Probando user_product PUT:")
    if upid:
        r2=requests.put(f"{API}/user-products/{upid}/stock",headers=HJ,json={"locations":[{"type":"selling","quantity":1}]},timeout=15)
        print(f"  user-products/stock HTTP {r2.status_code}: {r2.text[:400]}")

# Register in priority_replenish with default_qty=1
print("\n[SUPABASE] insertando en meli_priority_replenish:")
row={"item_id":ITEM,"account":"ASVA","default_qty":1}
rp=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
    headers={**SBH,"Prefer":"return=representation,resolution=merge-duplicates"},
    json=row,timeout=15)
print(f"  HTTP {rp.status_code}: {rp.text[:300]}")

# Also register directive
d={"account":"ASVA","scope":"item","scope_value":ITEM,
   "directive_type":"priority_replenish","value_numeric":1,
   "raw_user_message":"muestres en meli solo 1 a la venta pero quiero que cada 30 segundos se revise si cayo una venta y si cayo se reponga 1 stock 3849137034"}
rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,json=d,timeout=15)
print(f"\n[DIRECTIVE] HTTP {rd.status_code}: {rd.text[:200]}")

# Verify final state
print("\n[VERIFY]")
g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"  status={g2.get('status')} qty={g2.get('available_quantity')} inv={g2.get('inventory_id')}")

print("\n[DONE]")
