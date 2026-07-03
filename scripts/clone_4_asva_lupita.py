"""Clonar 4 items tradicionales ASVA → LUPITA con autostock qty=1"""
import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SEC=os.environ["MELI_APP_SECRET"]
RT_AS=os.environ["MELI_REFRESH_TOKEN_ASVA"]
RT_LU=os.environ["MELI_REFRESH_TOKEN_LUPITA"]
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}

def auth(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={
      "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SEC,"refresh_token":rt},timeout=20).json()["access_token"]

AT_AS=auth(RT_AS); AT_LU=auth(RT_LU)
H_AS={"Authorization":f"Bearer {AT_AS}","Content-Type":"application/json"}
H_LU={"Authorization":f"Bearer {AT_LU}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H_LU,timeout=10).json()
print(f"[auth] Lupita uid={me.get('id')}",flush=True)

TARGETS=["MLM2886030837","MLM5233480022","MLM5576391292","MLM3049333265"]
BLOCK={"ITEM_CONDITION","SELLER_SKU","UPC","UPC_ID","CATALOG_PRODUCT_ID","EMPTY_GTIN_REASON","IS_EMERGING_BRAND","IS_TOM_BRAND","IS_HIGHLIGHT_BRAND","AGE_GROUP"}
results=[]
for src_id in TARGETS:
    try:
        s=requests.get(f"https://api.mercadolibre.com/items/{src_id}?include_attributes=all",headers=H_AS,timeout=15).json()
        desc_r=requests.get(f"https://api.mercadolibre.com/items/{src_id}/description",headers=H_AS,timeout=10)
        desc_text=desc_r.json().get("plain_text","") if desc_r.status_code==200 else ""
        
        attrs=[]
        for a in s.get("attributes",[]):
            aid=a.get("id"); v=a.get("value_name")
            if not aid or not v or aid in BLOCK: continue
            attrs.append({"id":aid,"value_name":v})
        
        payload={
            "title":s.get("title"),
            "category_id":s.get("category_id"),
            "price":s.get("price"),
            "currency_id":"MXN",
            "available_quantity":1,
            "buying_mode":"buy_it_now",
            "listing_type_id":"gold_pro",
            "condition":s.get("condition","new"),
            "pictures":[{"source":p.get("secure_url") or p.get("url")} for p in s.get("pictures",[])[:12]],
            "attributes":attrs,
            "sale_terms":s.get("sale_terms",[]),
        }
        r=requests.post("https://api.mercadolibre.com/items",headers=H_LU,json=payload,timeout=30)
        if r.status_code in (200,201):
            new=r.json(); nid=new.get("id")
            results.append({"src":src_id,"new":nid,"price":new.get("price"),"status":new.get("status")})
            print(f"  {src_id} → {nid} status={new.get('status')} price=${new.get('price')}",flush=True)
            if desc_text and nid:
                requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=H_LU,json={"plain_text":desc_text},timeout=10)
            # Autostock
            requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
              json={"account":"LUPITA","item_id":nid,"default_qty":1,"product_name":(s.get('title') or '')[:60],"reason":f"Auto stock - clonado de ASVA {src_id}"},timeout=10)
            requests.post(f"{SB}/rest/v1/meli_user_directives",headers=SBH,
              json={"account":"LUPITA","scope":"item","scope_value":nid,"directive_type":"clone_from_asva","raw_user_message":f"Clonado {src_id} → {nid} ${new.get('price')}"},timeout=10)
        else:
            results.append({"src":src_id,"code":r.status_code,"error":r.text[:200]})
            print(f"  {src_id} FAIL {r.status_code}: {r.text[:150]}",flush=True)
        time.sleep(3)
    except Exception as e:
        results.append({"src":src_id,"exc":str(e)})
        print(f"  {src_id} EXC: {e}",flush=True)

print("\n=== SUMMARY ===",flush=True)
for r in results:
    if r.get("new"): print(f"  OK {r['src']} → {r['new']}",flush=True)
    else: print(f"  FAIL {r['src']}: {r.get('error') or r.get('exc')}",flush=True)
