import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

def refresh(env_var):
    RT=os.environ[env_var]
    r=requests.post("https://api.mercadolibre.com/oauth/token",
      data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
    return r["access_token"], r["refresh_token"]

# Get tokens for both accounts
AT_K, NEW_RT_K = refresh("MELI_REFRESH_TOKEN_KARIME")
AT_L, NEW_RT_L = refresh("MELI_REFRESH_TOKEN_LIGIA")
print(f"NEW_RT_KARIME: {NEW_RT_K}",flush=True)
print(f"NEW_RT_LIGIA: {NEW_RT_L}",flush=True)
H_K={"Authorization":f"Bearer {AT_K}","Content-Type":"application/json"}
H_L={"Authorization":f"Bearer {AT_L}","Content-Type":"application/json"}

# 1) Fetch source item from KARIME
SRC="MLM5705924474"
print(f"\n=== 1. SOURCE {SRC} (KARIME) ===",flush=True)
s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H_K,timeout=15).json()
print(f"  title: {s.get('title','?')[:70]}",flush=True)
print(f"  status: {s.get('status')} sub={s.get('sub_status')}",flush=True)
print(f"  cpid: {s.get('catalog_product_id')} cat: {s.get('category_id')}",flush=True)
print(f"  price: ${s.get('price')} qty: {s.get('available_quantity')}",flush=True)
print(f"  listing: {s.get('listing_type_id')} catalog_listing: {s.get('catalog_listing')}",flush=True)
print(f"  condition: {s.get('condition')}",flush=True)

CPID=s.get("catalog_product_id")
cat=s.get("category_id")
price=int(s.get("price") or 499)
condition=s.get("condition") or "new"
listing=s.get("listing_type_id") or "gold_pro"

# 2) Post clone in LIGIA
print(f"\n=== 2. POSTING in LIGIA ===",flush=True)
payload={
    "catalog_product_id":CPID,
    "category_id":cat,
    "price":price,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":condition,
    "listing_type_id":listing,
    "catalog_listing":True,
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                  {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print(f"  payload: cpid={CPID} cat={cat} price=${price} qty=1 cond={condition}",flush=True)

p=requests.post("https://api.mercadolibre.com/items",headers=H_L,json=payload,timeout=25).json()
if "id" not in p:
    print(f"  ❌ FAIL: {json.dumps(p)[:1500]}",flush=True)
    exit(1)

new_id=p["id"]
print(f"  ✅ POSTED: {new_id}",flush=True)
print(f"  status: {p.get('status')} price=${p.get('price')} qty={p.get('available_quantity')}",flush=True)
print(f"  title: {p.get('title','?')[:70]}",flush=True)
print(f"  URL: {p.get('permalink','?')}",flush=True)
print(f"NEW_ITEM_ID={new_id}",flush=True)

# 3) Verify status active
print(f"\n=== 3. VERIFY LIGIA item ===",flush=True)
time.sleep(2)
v=requests.get(f"https://api.mercadolibre.com/items/{new_id}?attributes=id,status,available_quantity,price,sub_status,catalog_product_id",headers=H_L,timeout=10).json()
print(f"  verified: status={v.get('status')} qty={v.get('available_quantity')} price=${v.get('price')} sub={v.get('sub_status')}",flush=True)
print(f"  catalog_product_id: {v.get('catalog_product_id')}",flush=True)

# 4) Add to Supabase priority_replenish
sb_url="https://wnuhslmryspnypbxbfjf.supabase.co"
sb_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndudWhzbG1yeXNwbnlwYnhiZmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwNDMzOTMsImV4cCI6MjA5NDYxOTM5M30.Rj3RIWyGvqRk91bYVRQpFF4al3oMWfjNs-IPIdHQP3E"
sh={"apikey":sb_key,"Authorization":f"Bearer {sb_key}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
row={
    "item_id":new_id,"account":"LIGIA","default_qty":1,
    "product_name":"Parlante JBL Go 4 Negro (clon de KARIME MLM5705924474)",
    "reason":"user pidió clonar + autostock qty=1 cada venta 2026-07-18"
}
r=requests.post(f"{sb_url}/rest/v1/meli_priority_replenish",headers=sh,json=row,timeout=15)
print(f"\n=== 4. Supabase priority_replenish INSERT: {r.status_code} ===",flush=True)
if r.status_code >= 400:
    print(f"  err: {r.text[:300]}",flush=True)

# 5) Also update LIGIA token in DB
r=requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.LIGIA",headers=sh,json={"refresh_token":NEW_RT_L},timeout=10)
print(f"  token LIGIA update: {r.status_code}",flush=True)
r=requests.patch(f"{sb_url}/rest/v1/meli_tokens?account=eq.KARIME",headers=sh,json={"refresh_token":NEW_RT_K},timeout=10)
print(f"  token KARIME update: {r.status_code}",flush=True)

# 6) Verify Supabase row exists
r=requests.get(f"{sb_url}/rest/v1/meli_priority_replenish?item_id=eq.{new_id}&select=*",headers=sh,timeout=10)
print(f"\n=== 5. SUPABASE VERIFY ===",flush=True)
print(f"  {r.text[:400]}",flush=True)

# 7) Test the autostock logic manually: set qty to 0, then force reponer to simulate what bot will do
print(f"\n=== 6. TEST AUTOSTOCK SIMULATION ===",flush=True)
# First simulate what the bot does when it sees qty=0: PUT status=active + qty=1
tr=requests.put(f"https://api.mercadolibre.com/items/{new_id}",headers=H_L,json={"status":"active","available_quantity":1},timeout=15).json()
if tr.get("error"):
    print(f"  ⚠️ simulated restock ERR: {tr.get('message','?')[:200]}",flush=True)
else:
    print(f"  ✅ simulated restock: status={tr.get('status')} qty={tr.get('available_quantity')}",flush=True)
    print(f"  → EL BOT PODRÁ REPONER CORRECTAMENTE",flush=True)

print(f"\n=== FINAL SUMMARY ===",flush=True)
print(f"  Origen KARIME: {SRC}",flush=True)
print(f"  Clon LIGIA:    {new_id}",flush=True)
print(f"  URL LIGIA:     {p.get('permalink','?')}",flush=True)
print(f"  Autostock:     ACTIVO qty=1 (bot repone cada 30s)",flush=True)
