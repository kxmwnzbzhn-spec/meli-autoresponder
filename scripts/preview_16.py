import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

ITEMS=["MLM5569282738","MLM3045607131","MLM3045609271","MLM5569353088",
       "MLM5569446604","MLM5569350350","MLM3045615611","MLM5569353878",
       "MLM3045609843","MLM5569359030","MLM3045613145","MLM3059642403",
       "MLM5569408564","MLM5569444970","MLM3048991273","MLM3054168351"]

# Get category names for cats
cat_names={}
def cat_name(cid):
    if cid in cat_names: return cat_names[cid]
    try:
        c=requests.get(f"https://api.mercadolibre.com/categories/{cid}",timeout=8).json()
        n=c.get("name","?")
        cat_names[cid]=n
        return n
    except:
        return cid

print(f"\n{'ITEM':<15} {'TITLE':<45} {'CPID':<15} {'CAT':<28} {'PRICE':>8} {'QTY':>5} {'COND':<10} {'STATUS':<10}",flush=True)
print("-"*160,flush=True)
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,catalog_product_id,category_id,price,available_quantity,condition,status,listing_type_id,catalog_listing",headers=H,timeout=10).json()
    if g.get("error"):
        print(f"{iid:<15} ERR: {g.get('message','?')[:80]}",flush=True)
        continue
    title=(g.get("title") or "?")[:44]
    cpid=g.get("catalog_product_id") or "-"
    catid=g.get("category_id") or "-"
    catn=cat_name(catid)
    price=g.get("price") or 0
    qty=g.get("available_quantity") or 0
    cond=g.get("condition") or "?"
    st=g.get("status") or "?"
    lt=g.get("listing_type_id") or "?"
    is_cat=" CATALOG" if g.get("catalog_listing") else ""
    print(f"{iid:<15} {title:<45} {cpid:<15} {catn[:27]:<28} ${price:>7,.0f} {qty:>5} {cond:<10} {st:<10}{is_cat}",flush=True)
