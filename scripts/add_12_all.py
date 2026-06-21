import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

ACC={
  "AH":"MELI_REFRESH_TOKEN_AH","ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL",
  "WILBERT":"MELI_REFRESH_TOKEN_WILBERT","JUAN":"MELI_REFRESH_TOKEN_JUAN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
  "MAYRELY":"MELI_REFRESH_TOKEN_MAYRELY","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW",
  "ADRIAN":"MELI_REFRESH_TOKEN_ADRIAN","ANGEL":"MELI_REFRESH_TOKEN_ANGEL",
  "ANGEL_DAMIAN":"MELI_REFRESH_TOKEN_ANGEL_DAMIAN","ASGARI":"MELI_REFRESH_TOKEN_ASGARI",
  "MC":"MELI_REFRESH_TOKEN_MC","OFICIAL":"MELI_REFRESH_TOKEN_OFICIAL",
  "USER1668":"MELI_REFRESH_TOKEN_USER1668","RAYMUNDO_MAY":"MELI_REFRESH_TOKEN_RAYMUNDO_MAY",
  "RMAYCHI":"MELI_REFRESH_TOKEN_RMAYCHI","BREN":"MELI_REFRESH_TOKEN_BREN",
  "MILDRED":"MELI_REFRESH_TOKEN_MILDRED","DILCIE":"MELI_REFRESH_TOKEN_DILCIE",
}
TOKENS={}
for n,k in ACC.items():
  rt=os.environ.get(k)
  if not rt: continue
  try:
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
    if r.status_code<400: TOKENS[n]=r.json()["access_token"]
  except: pass
print(f"tokens loaded: {sorted(TOKENS.keys())}")

IIDS=["MLM2806480091","MLM2826889323","MLM2826900247","MLM2828128921","MLM5093795526","MLM2828128345","MLM2790091203","MLM2827955087","MLM5106277224","MLM2789907229","MLM2826880153","MLM2789906859"]

rows=[]
for IID in IIDS:
  hit=None
  for n,AT in TOKENS.items():
    try:
      g=requests.get(f"{API}/items/{IID}",headers={"Authorization":f"Bearer {AT}"},timeout=12)
      if g.status_code==200:
        hit=(n,AT,g.json()); break
    except: pass
  if not hit:
    print(f"  ✗ {IID}: NOT accessible by any of {len(TOKENS)} tokens")
    continue
  acct,AT,info=hit
  attrs={a.get("id"):a.get("value_name") for a in info.get("attributes",[])}
  pics=info.get("pictures",[])
  filled=sum(1 for v in attrs.values() if v)
  dr=requests.get(f"{API}/items/{IID}/description",headers={"Authorization":f"Bearer {AT}"},timeout=15)
  desc=(dr.json().get("plain_text","") if dr.status_code==200 else "")[:5000]
  rows.append({
    "item_id":IID,"source_account":acct,"title":info.get("title"),"price":info.get("price"),
    "category_id":info.get("category_id"),"catalog_product_id":info.get("catalog_product_id"),
    "brand":attrs.get("BRAND"),"model":attrs.get("MODEL"),
    "color":attrs.get("MAIN_COLOR") or attrs.get("COLOR"),
    "condition":info.get("condition"),"has_complete_attributes":filled>=15,
    "photo_count":len(pics),"permalink":info.get("permalink"),
    "status":info.get("status"),"description_text":desc,
    "pic_urls":[p.get("secure_url") or p.get("url") for p in pics if p.get("url")],
    "attributes_json":[{"id":a["id"],"value_id":a.get("value_id"),"value_name":a.get("value_name")} for a in info.get("attributes",[]) if a.get("value_name") or a.get("value_id")],
    "sale_terms_json":[{"id":s["id"],"value_name":s.get("value_name")} for s in info.get("sale_terms",[])],
    "listing_type_id":info.get("listing_type_id"),
    "catalog_listing":bool(info.get("catalog_listing")),
    "shipping_json":info.get("shipping"),
    "attribute_count":filled,
    "last_synced":"2026-06-21T13:10:00Z"
  })
  print(f"  ✓ {IID} ({acct}) ${info.get('price')} {(info.get('title','') or '')[:60]}")

print(f"\nfetched {len(rows)} items")
SB=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
HS={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
if rows:
  resp=requests.post(f"{SB}/rest/v1/meli_clonable_catalog",headers=HS,json=rows,timeout=30)
  print(f"supabase: {resp.status_code} {resp.text[:300]}")
