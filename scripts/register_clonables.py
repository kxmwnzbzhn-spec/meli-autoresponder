import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

# Token map - try AH first, fallback to others if 403
TOKENS={}
for acct,key in [("AH","MELI_REFRESH_TOKEN_AH"),("WILBERT","MELI_REFRESH_TOKEN_WILBERT")]:
  rt=os.environ.get(key)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  if r.status_code<400:
    TOKENS[acct]=r.json()["access_token"]
    print(f"  ✓ {acct}")

SB_URL=os.environ["SUPABASE_URL"]
SB_KEY=os.environ["SUPABASE_SERVICE_KEY"]
HS={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}

# Get all rows that need enrichment
rows=requests.get(f"{SB_URL}/rest/v1/meli_clonable_catalog?select=id,item_id,catalog_product_id,source_account&item_id=not.is.null&order=id.asc",headers=HS,timeout=30).json()
print(f"\nrows to enrich: {len(rows)}")

updates=[]
for row in rows:
  iid=row["item_id"]
  acct=row.get("source_account") or "AH"
  AT=TOKENS.get(acct) or TOKENS.get("AH")
  H={"Authorization":f"Bearer {AT}"}
  
  g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
  if g.get("status")==403 or g.get("error"):
    # Try alt tokens
    for alt in TOKENS.values():
      g2=requests.get(f"{API}/items/{iid}",headers={"Authorization":f"Bearer {alt}"},timeout=15).json()
      if not g2.get("error"):
        g=g2; break
  
  if g.get("error"):
    print(f"  ✗ {iid}: {g.get('message','?')[:60]}")
    continue
  
  # Get description
  dr=requests.get(f"{API}/items/{iid}/description",headers=H,timeout=10)
  desc=dr.json().get("plain_text","") if dr.status_code==200 else ""
  
  attrs=g.get("attributes",[])
  pics=g.get("pictures",[])
  
  payload={
    "description_text": desc,
    "pic_urls": [p.get("secure_url") or p.get("url") for p in pics if p.get("url")],
    "attributes_json": [{"id":a["id"],"value_id":a.get("value_id"),"value_name":a.get("value_name")} for a in attrs if (a.get("value_name") or a.get("value_id"))],
    "sale_terms_json": [{"id":s["id"],"value_name":s.get("value_name")} for s in g.get("sale_terms",[])],
    "listing_type_id": g.get("listing_type_id"),
    "catalog_listing": bool(g.get("catalog_listing")),
    "shipping_json": g.get("shipping"),
    "attribute_count": sum(1 for a in attrs if a.get("value_name") or a.get("value_id")),
    "last_synced": "now()",
    "title": g.get("title"),
    "price": g.get("price"),
    "category_id": g.get("category_id"),
    "condition": g.get("condition"),
    "status": g.get("status"),
    "permalink": g.get("permalink"),
    "photo_count": len(pics),
    "has_complete_attributes": sum(1 for a in attrs if a.get("value_name") or a.get("value_id"))>=15,
  }
  
  # PATCH this row
  pr=requests.patch(f"{SB_URL}/rest/v1/meli_clonable_catalog?id=eq.{row['id']}",headers={**HS,"Prefer":"return=minimal"},json=payload,timeout=20)
  status="✓" if pr.status_code in (200,204) else f"✗ {pr.status_code}"
  print(f"  {status} {iid} | desc={len(desc)} pics={len(pics)} attrs={payload['attribute_count']}")

# Also sync CPID-only rows with category prediction
cpids=requests.get(f"{SB_URL}/rest/v1/meli_clonable_catalog?select=id,catalog_product_id&item_id=is.null",headers=HS,timeout=30).json()
print(f"\nCPID-only to enrich: {len(cpids)}")
AT=TOKENS.get("AH")
H={"Authorization":f"Bearer {AT}"}
for row in cpids:
  cpid=row["catalog_product_id"]
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  pics_cpid=cp.get("pictures",[])
  pr=requests.patch(f"{SB_URL}/rest/v1/meli_clonable_catalog?id=eq.{row['id']}",headers={**HS,"Prefer":"return=minimal"},
    json={
      "pic_urls":[p.get("url") for p in pics_cpid if p.get("url")],
      "attributes_json":[{"id":a.get("id"),"value_name":a.get("value_name"),"value_id":a.get("value_id")} for a in cp.get("attributes",[]) if a.get("value_name")],
      "listing_type_id":"gold_pro",
      "catalog_listing":True,
      "last_synced":"now()",
    },timeout=20)
  print(f"  {pr.status_code} {cpid} pics={len(pics_cpid)}")
