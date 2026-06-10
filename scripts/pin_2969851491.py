import os, requests, json, sys
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; NEW_RT=tok["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
IID="MLM2969851491"; PRICE=1199
# read current
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print(f"[BEFORE] price={g.get('price')} cpid={g.get('catalog_product_id')} status={g.get('status')} title={g.get('title')[:60]}")
# PUT price
p=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"price":PRICE},timeout=20)
print(f"[PUT price] HTTP {p.status_code}")
if p.status_code>=300: print(p.text[:500])
# verify
g2=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print(f"[AFTER] price={g2.get('price')} cpid={g2.get('catalog_product_id')}")
# Supabase directives + strategy
SB_URL=os.environ.get("SUPABASE_URL"); SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY")
if SB_URL and SB_KEY:
  HSB={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=representation"}
  cpid=g2.get("catalog_product_id")
  scope_val=cpid or IID
  d={"account":"adrian","scope":"catalog_product_id" if cpid else "item_id",
     "scope_value":scope_val,"directive_type":"pin_price","value_numeric":PRICE,
     "raw_user_message":"ahora este precio $1199 2969851491"}
  rd=requests.post(f"{SB_URL}/rest/v1/meli_user_directives",headers=HSB,json=d,timeout=15)
  print(f"[SB directive] HTTP {rd.status_code}")
  if cpid:
    # upsert strategy floor=ceiling=PRICE
    up={"floor":PRICE,"ceiling":PRICE}
    ru=requests.patch(f"{SB_URL}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}",
        headers=HSB,json=up,timeout=15)
    print(f"[SB strategy patch] HTTP {ru.status_code} body_len={len(ru.text)}")
    if ru.status_code==200 and ru.text in ("[]","null"):
      # insert
      ins={"catalog_product_id":cpid,"floor":PRICE,"ceiling":PRICE,"target":PRICE,"account":"adrian"}
      ri=requests.post(f"{SB_URL}/rest/v1/meli_catalog_strategy",headers=HSB,json=ins,timeout=15)
      print(f"[SB strategy insert] HTTP {ri.status_code}")
