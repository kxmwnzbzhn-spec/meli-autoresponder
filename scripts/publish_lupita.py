"""Publish 20 catalog items in LUPITA account with autostock qty=1"""
import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]
RT_L=os.environ["MELI_REFRESH_TOKEN_LUPITA"]
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}

TARGETS=[
  ("MLM2022828333",1199),("MLM50444272",2290),("MLM66806041",499),
  ("MLM2021493918",1199),("MLM2021495500",1199),("MLM41991186",699),
  ("MLM61262890",499),("MLM44710240",499),("MLM44710313",499),
  ("MLM2020109296",1199),("MLM37361021",499),("MLM65056521",499),
  ("MLM46998439",499),("MLM69907677",1999),("MLM63973616",499),
  ("MLM2021121410",999),("MLM49608224",2050),("MLM68969359",504),
  ("MLM70607552",599),("MLM25912333",690),
]

# Auth Lupita
r=requests.post("https://api.mercadolibre.com/oauth/token",data={
  "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":RT_L},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
print(f"[auth] Lupita uid={me.get('id')} nick={me.get('nickname')}",flush=True)

results=[]
for cpid,price in TARGETS:
  try:
    # Get catalog product info for category
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=10).json()
    cat=(pd.get("settings",{}) or {}).get("category_id") or "MLM59800"
    payload={
      "catalog_listing":True,"catalog_product_id":cpid,"category_id":cat,
      "price":price,"currency_id":"MXN","buying_mode":"buy_it_now",
      "listing_type_id":"gold_pro","condition":"new","available_quantity":1,
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=30)
    if r.status_code in (200,201):
      new=r.json()
      new_id=new.get("id")
      results.append({"cpid":cpid,"new":new_id,"price":price,"status":new.get("status")})
      print(f"  {cpid} → {new_id} ${price} status={new.get('status')}",flush=True)
      # Add to priority_replenish
      if new_id:
        requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
          json={"account":"LUPITA","item_id":new_id,"default_qty":1,"product_name":cpid,"reason":"Auto stock continuo - clon Mayrely cerrada 2026-07-03"},timeout=10)
        # Register in user_directives
        requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
          json={"account":"LUPITA","scope":"item","scope_value":new_id,"directive_type":"published_catalog","raw_user_message":f"Publicado {cpid} → {new_id} ${price} desde lista usuario"},timeout=10)
    else:
      results.append({"cpid":cpid,"fail":r.text[:150],"code":r.status_code})
      print(f"  {cpid} FAIL {r.status_code}: {r.text[:120]}",flush=True)
    time.sleep(3)
  except Exception as e:
    results.append({"cpid":cpid,"exc":str(e)})
    print(f"  {cpid} EXC: {e}",flush=True)

ok=sum(1 for r in results if r.get("new"))
print(f"\n=== SUMMARY: {ok}/{len(TARGETS)} OK ===",flush=True)
print(json.dumps(results,indent=2,default=str),flush=True)
