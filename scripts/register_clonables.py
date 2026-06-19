import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

CPIDS=list(dict.fromkeys(["MLM44742234","MLM61289463","MLM47001347","MLM46404992"]))
print(f"unique CPIDs: {len(CPIDS)}")

rows=[]
for cpid in CPIDS:
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  name=cp.get("name","")
  print(f"\n=== {cpid} ===")
  print(f"  name: {name}")
  print(f"  domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')}")
  # Get attributes
  attr_map={}
  for a in cp.get("attributes",[]):
    attr_map[a.get("id")]=a.get("value_name")
  brand=attr_map.get("BRAND")
  model=attr_map.get("MODEL")
  color=attr_map.get("MAIN_COLOR") or attr_map.get("COLOR")
  print(f"  brand={brand} model={model} color={color}")
  # Snapshot competition
  i=requests.get(f"{API}/products/{cpid}/items?limit=10",headers=H,timeout=15).json()
  ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
  ps.sort()
  if ps:
    print(f"  competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")
  pics=cp.get("pictures",[])
  rows.append({
    "item_id": None,
    "source_account": None,
    "title": name[:200],
    "price": None,
    "category_id": None,
    "catalog_product_id": cpid,
    "brand": brand,
    "model": model,
    "color": color,
    "condition": "new",
    "has_complete_attributes": False,
    "photo_count": len(pics),
    "permalink": f"https://www.mercadolibre.com.mx/p/{cpid}",
    "status": "pending",
    "notes": f"CPID-only entry. Min competidor: ${ps[0] if ps else 'sin data'} | Pics CPID: {len(pics)}",
    "tags": ["cpid_only","ready_to_publish"]
  })

SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY","")
if SB_URL and SB_KEY:
  HS={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json"}
  resp=requests.post(f"{SB_URL}/rest/v1/meli_clonable_catalog",headers=HS,json=rows,timeout=30)
  print(f"\nsupabase POST: {resp.status_code}")
  print(resp.text[:500])
