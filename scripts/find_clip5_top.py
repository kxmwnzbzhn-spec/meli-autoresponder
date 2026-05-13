import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

def search_catalog_products(query):
    # Catalog products search
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(query)}&limit=20"
    r=requests.get(url,headers=H).json()
    return r

def get_product_items(cpid):
    # listings competing on this catalog
    url=f"https://api.mercadolibre.com/products/{cpid}/items"
    r=requests.get(url,headers=H).json()
    return r

def find_top(query):
    print(f"\n========== {query} ==========")
    r=search_catalog_products(query)
    results=r.get("results",[])
    print(f"Catalog products found: {len(results)}")
    for p in results[:10]:
        cpid=p.get("id")
        name=p.get("name","")
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        color=attrs.get("COLOR","")
        domain=p.get("domain_id","")
        status=p.get("status","")
        sold=None
        # try GET /products/{cpid}
        try:
            pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
            sold=pd.get("buy_box_winner",{}).get("sold_quantity") if pd.get("buy_box_winner") else None
        except: pass
        print(f"  CPID={cpid}  COLOR={color}  status={status}")
        print(f"     name={name}")
        print(f"     domain={domain}")
        if sold is not None: print(f"     buy_box_sold={sold}")

find_top("jbl clip 5 camuflaje")
find_top("jbl clip 5 azul rosa")
find_top("jbl clip 5 squad")
