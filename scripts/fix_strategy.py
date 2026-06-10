import os, requests
SB=os.environ["SUPABASE_URL"]; K=os.environ["SUPABASE_SERVICE_KEY"]
H={"apikey":K,"Authorization":f"Bearer {K}","Content-Type":"application/json","Prefer":"return=representation"}
# Inspect a known row to see columns
r=requests.get(f"{SB}/rest/v1/meli_catalog_strategy?select=*&limit=1",headers=H,timeout=15)
print("sample:",r.text[:500])
# Try insert minimal
for attempt in [
  {"catalog_product_id":"MLM3821813","floor":1199,"ceiling":1199},
  {"catalog_product_id":"MLM3821813","floor":1199,"ceiling":1199,"target_price":1199},
  {"catalog_product_id":"MLM3821813","floor":1199,"ceiling":1199,"sku":"DG-LIGHTBLUE-125"},
]:
  r=requests.post(f"{SB}/rest/v1/meli_catalog_strategy",headers=H,json=attempt,timeout=15)
  print("insert",attempt,"->",r.status_code,r.text[:200])
  if r.status_code in (201,200): break
