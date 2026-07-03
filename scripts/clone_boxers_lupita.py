"""
Clonar 3 CK Boxers de ASVA (MLM5607789818 S, MLM3066095021 M, MLM3066033037 L) → LUPITA
- Copiar size chart de ASVA como propio de Lupita
- Publicar 3 items con family_name compartido
- Cada uno qty=1 + autostock priority_replenish
"""
import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]
RT_AS=os.environ["MELI_REFRESH_TOKEN_ASVA"]
RT_LU=os.environ["MELI_REFRESH_TOKEN_LUPITA"]
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}

def auth(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=20).json()
    return r["access_token"]

AT_AS=auth(RT_AS); AT_LU=auth(RT_LU)
H_AS={"Authorization":f"Bearer {AT_AS}","Content-Type":"application/json"}
H_LU={"Authorization":f"Bearer {AT_LU}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H_LU,timeout=10).json()
print(f"[auth] Lupita uid={me.get('id')} nick={me.get('nickname')}",flush=True)

# 1) Get ASVA S item to copy the size chart id
src_s=requests.get("https://api.mercadolibre.com/items/MLM5607789818?include_attributes=all",headers=H_AS,timeout=15).json()
asva_grid_id=next((a.get("value_name") for a in src_s.get("attributes",[]) if a.get("id")=="SIZE_GRID_ID"),None)
print(f"[grid] ASVA size grid: {asva_grid_id}",flush=True)

# 2) Copy chart to LUPITA
chart=requests.get(f"https://api.mercadolibre.com/catalog/charts/{asva_grid_id}",headers=H_AS,timeout=10).json()
chart.pop("id",None); chart.pop("seller_id",None)
for r in chart.get("rows",[]): r.pop("id",None)
r=requests.post("https://api.mercadolibre.com/catalog/charts",headers=H_LU,json=chart,timeout=20).json()
lu_grid_id=r["id"]
lu_rows=[row["id"] for row in r.get("rows",[])]
print(f"[grid] Lupita size grid created: {lu_grid_id} rows={lu_rows}",flush=True)

# 3) Publish 3 items in Lupita with same family_name
FAMILY="Calvin Klein Pack 3 Boxers Microfibra Hombre Premium Set 3"
size_map=[
  ("S","16235918",lu_rows[0],"MLM5607789818"),
  ("M","2282666", lu_rows[1],"MLM3066095021"),
  ("L","24460276",lu_rows[2],"MLM3066033037"),
]

# Base attributes from ASVA S
src_attrs=src_s.get("attributes",[])
BLOCK={"SIZE_GRID_ID","SIZE_GRID_ROW_ID","FILTRABLE_SIZE","AGE_GROUP","IS_EMERGING_BRAND","IS_TOM_BRAND","IS_HIGHLIGHT_BRAND","SELLER_SKU","ITEM_CONDITION","CATALOG_PRODUCT_ID","EMPTY_GTIN_REASON","UPC","UPC_ID","SIZE"}
base_attrs=[]
for a in src_attrs:
  if a.get("id") in BLOCK: continue
  if not a.get("value_name"): continue
  base_attrs.append({"id":a["id"],"value_name":a["value_name"]})
pictures=[{"source":p.get("secure_url") or p.get("url")} for p in src_s.get("pictures",[])[:12]]
sale_terms=src_s.get("sale_terms",[])

# Get description from ASVA S
desc_r=requests.get(f"https://api.mercadolibre.com/items/MLM5607789818/description",headers=H_AS,timeout=10)
desc_text=desc_r.json().get("plain_text","") if desc_r.status_code==200 else ""

new_ids=[]
for size,size_vid,row_id,src_id in size_map:
    payload={
      "family_name":FAMILY,
      "category_id":src_s.get("category_id","MLM194115"),
      "price":src_s.get("price",399),
      "currency_id":"MXN","buying_mode":"buy_it_now",
      "listing_type_id":"gold_pro","condition":"new",
      "available_quantity":1,
      "pictures":pictures,
      "attributes":base_attrs+[
        {"id":"SIZE","value_id":size_vid,"value_name":size},
        {"id":"SIZE_GRID_ID","value_name":lu_grid_id},
        {"id":"SIZE_GRID_ROW_ID","value_name":row_id}
      ],
      "sale_terms":sale_terms
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H_LU,json=payload,timeout=30)
    if r.status_code in (200,201):
        new=r.json(); nid=new.get("id")
        new_ids.append((size,nid))
        print(f"  SIZE {size} → {nid} status={new.get('status')} price=${new.get('price')}",flush=True)
        # Description
        if desc_text and nid:
            requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_LU,json={"plain_text":desc_text},timeout=10)
        # Autostock
        requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
          json={"account":"LUPITA","item_id":nid,"default_qty":1,"product_name":f"CK Boxers {size}","reason":"Auto stock continuo - clonado desde ASVA"},timeout=10)
        requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
          json={"account":"LUPITA","scope":"item","scope_value":nid,"directive_type":"clone_boxers","raw_user_message":f"Clonado {src_id} → {nid} CK Boxers talla {size}"},timeout=10)
    else:
        print(f"  SIZE {size} FAIL {r.status_code}: {r.text[:200]}",flush=True)
    time.sleep(3)

print(f"\n=== SUMMARY ===",flush=True)
for s,i in new_ids: print(f"  {s}: {i}",flush=True)
