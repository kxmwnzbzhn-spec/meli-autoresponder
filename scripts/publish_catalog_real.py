"""Try publishing MLM61262890 as TRUE catalog_listing with various listing_type_id."""
import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

CPID="MLM61262890"
FLOOR=499; CEIL=549; PRICE=549

# Try each listing_type with minimal catalog payload
for lt in ["gold_pro","gold_premium","gold_special","gold","silver","bronze"]:
    print(f"\n=== Try listing_type_id={lt} ===")
    payload={
        "catalog_product_id":CPID,
        "catalog_listing":True,
        "price":PRICE,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"new",
        "listing_type_id":lt,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
    }
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
    print(f"  validate HTTP {rv.status_code}: {rv.text[:500]}")
    if rv.status_code in (200,204):
        # Real POST
        rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
        print(f"  POST HTTP {rp.status_code}: {rp.text[:800]}")
        if rp.status_code in (200,201):
            it=rp.json(); iid=it.get("id"); link=it.get("permalink")
            print(f"\n✅ CATALOG PUBLISHED {iid}")
            print(f"  Permalink: {link}")
            # Supabase ops
            for dt,val in [("set_floor",FLOOR),("set_ceiling",CEIL)]:
                for scope,sv in [("item",iid),("cpid",CPID)]:
                    requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                        json={"account":"CLARIBEL","scope":scope,"scope_value":sv,
                              "directive_type":dt,"value_numeric":val,
                              "raw_user_message":"publicame catalogo claribel 499-549"},timeout=10)
            requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{CPID}",
                headers={**SBH,"Prefer":"return=minimal"},
                json={"floor":FLOOR,"ceiling":CEIL,"active":True},timeout=10)
            requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                json={"item_id":iid,"account":"CLARIBEL","default_qty":1,
                      "product_name":"JBL Go 4 Celeste (catalog)"},timeout=10)
            print(f"  Supabase updated. Done.")
            break
