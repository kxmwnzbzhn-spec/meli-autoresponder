import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

IDS="""2976325463 5526819898 5486928204 5511173002 5511720082 5511732856 5525982716 5511745202 5510861004 5511771024 5511745192 5511745190 2999746371 5526817520 3025719815 5511758034 5511745194 3025478283 5511745198 5511758048 3018313225 3018413181 3014066043 3014067109 3014067125 3020492945 5510809004 5511082004 5525381774 3014080097 3014080133 3018014885 3025478179 3025478373 3025478557 5510679006 5510900004 5511027378 5511173004 5511212002 3025553813 5526806736""".split()
# Dedupe and prefix
ids=[f"MLM{x}" for x in dict.fromkeys(IDS)]
print(f"total unique: {len(ids)}")

# Batch fetch via multi-get
rows=[]
B=20
for i in range(0,len(ids),B):
  batch=ids[i:i+B]
  r=requests.get(f"{API}/items?ids={','.join(batch)}&attributes=id,title,price,status,sub_status,available_quantity,catalog_product_id,catalog_listing,category_id,condition,permalink,pictures,attributes,seller_id",headers=H,timeout=20).json()
  for entry in r:
    code=entry.get("code")
    body=entry.get("body",{})
    iid=body.get("id") or batch[0]
    if code!=200:
      print(f"  {iid}: HTTP {code} - {body.get('message','')[:80]}")
      continue
    attrs={a.get("id"):(a.get("value_name") or a.get("value_id")) for a in body.get("attributes",[])}
    brand=attrs.get("BRAND")
    model=attrs.get("MODEL")
    color=attrs.get("MAIN_COLOR") or attrs.get("COLOR")
    pics=body.get("pictures",[]) or []
    filled=sum(1 for v in attrs.values() if v)
    has_complete=filled>=15
    rows.append({
      "item_id": body.get("id"),
      "source_account":"AH",
      "title": body.get("title"),
      "price": body.get("price"),
      "category_id": body.get("category_id"),
      "catalog_product_id": body.get("catalog_product_id"),
      "brand": brand,
      "model": model,
      "color": color,
      "condition": body.get("condition"),
      "has_complete_attributes": has_complete,
      "photo_count": len(pics),
      "permalink": body.get("permalink"),
      "status": body.get("status"),
      "available_quantity": body.get("available_quantity"),
    })

print(f"fetched {len(rows)} rows")
print(json.dumps(rows,ensure_ascii=False,default=str)[:300])

# Send to Supabase via REST
SB_URL=os.environ.get("SUPABASE_URL","")
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY","")
if SB_URL and SB_KEY:
  HS={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
  # Strip available_quantity which isn't in schema
  for r in rows: r.pop("available_quantity",None)
  resp=requests.post(f"{SB_URL}/rest/v1/meli_clonable_catalog",headers=HS,json=rows,timeout=30)
  print(f"supabase POST: {resp.status_code}")
  print(resp.text[:500])
