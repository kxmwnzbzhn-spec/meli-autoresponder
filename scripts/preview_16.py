import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
if not r.get("access_token"):
    print(f"REFRESH ERR: {json.dumps(r)[:500]}",flush=True)
    exit()
AT=r["access_token"]
print(f"NEW_RT_MAYRELY: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

ITEMS=["MLM5569282738","MLM3045607131","MLM3045609271","MLM5569353088",
       "MLM5569446604","MLM5569350350","MLM3045615611","MLM5569353878",
       "MLM3045609843","MLM5569359030","MLM3045613145","MLM3059642403",
       "MLM5569408564","MLM5569444970","MLM3048991273","MLM3054168351"]

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

results=[]
print(f"\n=== PREVIEW ===\n",flush=True)
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,catalog_product_id,category_id,price,available_quantity,condition,status,listing_type_id,catalog_listing",headers=H,timeout=10).json()
    if g.get("error"):
        print(f"{iid} ERR: {g.get('message','?')[:80]}",flush=True)
        results.append((iid,None,None,None,None,None,None,None))
        continue
    title=(g.get("title") or "?")
    cpid=g.get("catalog_product_id")
    catid=g.get("category_id") or "-"
    catn=cat_name(catid)
    price=g.get("price") or 0
    qty=g.get("available_quantity") or 0
    cond=g.get("condition") or "?"
    st=g.get("status") or "?"
    lt=g.get("listing_type_id") or "?"
    is_cat=g.get("catalog_listing")
    results.append((iid,title,cpid,catid,catn,price,qty,cond,st,lt,is_cat))
    print(f"{iid} | title: {title[:60]}",flush=True)
    print(f"  cpid: {cpid} | cat: {catid} ({catn}) | price: ${price} | qty: {qty} | cond: {cond} | listing: {lt} | catalog_listing: {is_cat} | status: {st}",flush=True)
    print("",flush=True)
