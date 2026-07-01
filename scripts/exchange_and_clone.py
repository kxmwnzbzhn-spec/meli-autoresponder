"""
Intercambia OAuth code de Mildred → refresh_token + access_token.
Guarda en Supabase meli_tokens.
Luego clona 23 items Mayrely → Mildred con precios exactos.
"""
import os, requests, json, time, sys

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
CODE=os.environ["OAUTH_CODE"]
REDIRECT="https://oauth.pstmn.io/v1/callback"
SB_URL=os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY=os.environ["SUPABASE_SERVICE_KEY"]
RT_MC=os.environ["MELI_REFRESH_TOKEN_MC"]

SBH={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=representation"}

# 1) Exchange code
print(f"[oauth] APP_ID prefix={APP_ID[:4]}",flush=True)
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
  "grant_type":"authorization_code",
  "client_id":APP_ID,
  "client_secret":APP_SECRET,
  "code":CODE,
  "redirect_uri":REDIRECT
},timeout=25)
print(f"[oauth] status={r.status_code}",flush=True)
if r.status_code>=300:
  print(r.text[:500],flush=True)
  sys.exit(1)
j=r.json()
AT_MI=j["access_token"]; RT_MI=j["refresh_token"]; USER_MI=j["user_id"]
print(f"[oauth] user_id={USER_MI}",flush=True)

# 2) Store in Supabase meli_tokens (upsert MILDRED)
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {AT_MI}"},timeout=10).json()
NICK=me.get("nickname","?")
print(f"[user] nickname={NICK} name={me.get('first_name','')} {me.get('last_name','')}",flush=True)

# Delete old MILDRED if any
requests.delete(f"{SB_URL}/rest/v1/meli_tokens?account=eq.MILDRED",headers=SBH,timeout=10)
# Insert new
body={
  "account":"MILDRED",
  "meli_user_id":USER_MI,
  "access_token":AT_MI,
  "refresh_token":RT_MI,
  "expires_at":None,
  "active":True
}
r=requests.post(f"{SB_URL}/rest/v1/meli_tokens",headers=SBH,json=body,timeout=10)
print(f"[supabase] insert MILDRED status={r.status_code}",flush=True)

# 3) Auth MC using existing refresh token
r_mc=requests.post("https://api.mercadolibre.com/oauth/token",data={
  "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT_MC},timeout=20)
if r_mc.status_code>=300:
  # Fallback: use existing token from Supabase MC row
  print(f"[mc] refresh failed, using SB stored",flush=True)
  mc=requests.get(f"{SB_URL}/rest/v1/meli_tokens?account=eq.MC&select=access_token",headers=SBH,timeout=10).json()
  AT_MC=mc[0]["access_token"] if mc else None
else:
  AT_MC=r_mc.json()["access_token"]
print(f"[mc] AT set: {'yes' if AT_MC else 'NO'}",flush=True)

# 4) Clone 23 items
H_MC={"Authorization":f"Bearer {AT_MC}","Content-Type":"application/json"}
H_MI={"Authorization":f"Bearer {AT_MI}","Content-Type":"application/json"}

CATALOGO=[
  ("MLM3059642403",1199),("MLM3045612883",2290),("MLM3045609843",499),
  ("MLM3045613145",1199),("MLM5569408564",1199),("MLM3045615611",699),
  ("MLM5569282738",499),("MLM3045514191",499),("MLM3045607131",499),
  ("MLM5569359030",1199),("MLM5569400988",499),("MLM3045609271",499),
  ("MLM5569353088",499),("MLM5569443994",1999),("MLM5569353878",499),
  ("MLM5569444970",999),("MLM5569443364",2050),("MLM5569350350",504),
  ("MLM3045606657",599),("MLM5569446604",690),
]
TRADICIONAL=[
  ("MLM5575746082",299),("MLM5586829422",499),("MLM3054168351",399),
]

results={"catalogo":[],"tradicional":[],"fail":[]}

print(f"\n=== CATALOGO ({len(CATALOGO)}) ===",flush=True)
for src_id,price in CATALOGO:
  try:
    s=requests.get(f"https://api.mercadolibre.com/items/{src_id}?attributes=id,catalog_product_id,category_id",headers=H_MC,timeout=12).json()
    cpid=s.get("catalog_product_id")
    if not cpid:
      results["fail"].append({"src":src_id,"reason":"no cpid"}); print(f"  {src_id} FAIL no cpid",flush=True); continue
    payload={
      "catalog_listing":True,"catalog_product_id":cpid,
      "category_id":s.get("category_id","MLM59800"),
      "price":price,"currency_id":"MXN","buying_mode":"buy_it_now",
      "listing_type_id":"gold_pro","condition":"new","available_quantity":1,
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H_MI,json=payload,timeout=30)
    if r.status_code in (200,201):
      new=r.json()
      results["catalogo"].append({"src":src_id,"new":new.get("id"),"cpid":cpid,"price":price,"status":new.get("status")})
      print(f"  {src_id} → {new.get('id')} ${price} status={new.get('status')}",flush=True)
    else:
      results["fail"].append({"src":src_id,"reason":r.text[:180]}); print(f"  {src_id} FAIL {r.status_code}: {r.text[:100]}",flush=True)
    time.sleep(3)
  except Exception as e:
    results["fail"].append({"src":src_id,"reason":str(e)}); print(f"  {src_id} EXC: {e}",flush=True)

print(f"\n=== TRADICIONAL USADAS ({len(TRADICIONAL)}) ===",flush=True)
for src_id,price in TRADICIONAL:
  try:
    s=requests.get(f"https://api.mercadolibre.com/items/{src_id}?include_attributes=all",headers=H_MC,timeout=15).json()
    desc_r=requests.get(f"https://api.mercadolibre.com/items/{src_id}/description",headers=H_MC,timeout=10)
    desc_text=desc_r.json().get("plain_text","") if desc_r.status_code==200 else ""
    attrs=[]
    for a in s.get("attributes",[]):
      aid=a.get("id"); v=a.get("value_name")
      if not aid or not v: continue
      if aid in ("ITEM_CONDITION","SELLER_SKU","UPC","UPC_ID","CATALOG_PRODUCT_ID","EMPTY_GTIN_REASON","IS_EMERGING_BRAND","IS_TOM_BRAND","IS_HIGHLIGHT_BRAND","AGE_GROUP"): continue
      attrs.append({"id":aid,"value_name":v})
    payload={
      "title":s.get("title"),"category_id":s.get("category_id"),
      "price":price,"currency_id":"MXN","available_quantity":1,
      "buying_mode":"buy_it_now","listing_type_id":"gold_pro",
      "condition":s.get("condition","used"),
      "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in s.get("pictures",[])[:12]],
      "attributes":attrs,"sale_terms":s.get("sale_terms",[]),
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H_MI,json=payload,timeout=30)
    if r.status_code in (200,201):
      new=r.json(); new_id=new.get("id")
      results["tradicional"].append({"src":src_id,"new":new_id,"price":price,"status":new.get("status")})
      print(f"  {src_id} → {new_id} ${price} status={new.get('status')}",flush=True)
      if desc_text and new_id:
        requests.post(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H_MI,json={"plain_text":desc_text},timeout=15)
    else:
      results["fail"].append({"src":src_id,"reason":r.text[:180]}); print(f"  {src_id} FAIL {r.status_code}: {r.text[:100]}",flush=True)
    time.sleep(3)
  except Exception as e:
    results["fail"].append({"src":src_id,"reason":str(e)}); print(f"  {src_id} EXC: {e}",flush=True)

# 5) priority_replenish + user_directives
SBH2={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal"}
for x in results["catalogo"]+results["tradicional"]:
  if x.get("new"):
    requests.post(f"{SB_URL}/rest/v1/meli_priority_replenish",headers=SBH2,
      json={"account":"MILDRED","item_id":x["new"],"default_qty":1,"product_name":x.get("src",""),"reason":"Auto stock continuo - clon Mayrely"},timeout=10)
    requests.post(f"{SB_URL}/rest/v1/meli_user_directives",headers=SBH2,
      json={"account":"MILDRED","scope":"item","scope_value":x["new"],"directive_type":"clone_from_mayrely","raw_user_message":f"Cloned {x['src']} → {x['new']} ${x['price']}"},timeout=10)

print(f"\n=== SUMMARY ===",flush=True)
print(f"CATALOGO OK: {len(results['catalogo'])}/{len(CATALOGO)}",flush=True)
print(f"TRADICIONAL OK: {len(results['tradicional'])}/{len(TRADICIONAL)}",flush=True)
print(f"FAILS: {len(results['fail'])}",flush=True)
print(json.dumps(results,indent=2,default=str),flush=True)
