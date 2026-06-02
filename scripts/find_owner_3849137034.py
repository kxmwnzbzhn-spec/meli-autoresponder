import os, requests, sys
API="https://api.mercadolibre.com"

ACCS=[
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("MC","MELI_REFRESH_TOKEN_MC"),
  ("AHA","MELI_REFRESH_TOKEN_OFICIAL"),
  ("ANGEL_DAMIAN","MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
  ("ASGARI","MELI_REFRESH_TOKEN_ASGARI"),
  ("YC_NEW","MELI_REFRESH_TOKEN"),  # YC_NEW uses generic
  ("RAYMUNDO_MAY","MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
]
ITEM="MLM3849137034"
for nick,sec in ACCS:
    rt=os.environ.get(sec)
    if not rt: continue
    try:
        r=requests.post(f"{API}/oauth/token",data={
          "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
          "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=15).json()
        at=r.get("access_token")
        if not at: 
            print(f"{nick}: oauth err {r}"); continue
        h={"Authorization":f"Bearer {at}"}
        g=requests.get(f"{API}/items/{ITEM}",headers=h,timeout=10).json()
        if g.get("id")==ITEM and not g.get("error"):
            sid=g.get("seller_id")
            me=requests.get(f"{API}/users/me",headers=h,timeout=8).json()
            if me.get("id")==sid:
                print(f">>> OWNER={nick} | seller_id={sid} | status={g.get('status')} sub={g.get('sub_status')} | price={g.get('price')} | qty={g.get('available_quantity')} | inventory_id={g.get('inventory_id')} | title={g.get('title')[:80]}")
                # also show seller_sku
                attrs={a.get('id'):a.get('value_name') for a in (g.get('attributes') or [])}
                print(f"    sku={attrs.get('SELLER_SKU')} cpid={g.get('catalog_product_id')}")
                sys.exit(0)
            else:
                # not this seller
                pass
    except Exception as e:
        print(f"{nick}: EXC {e}")
print("NOT FOUND in any account tried")
