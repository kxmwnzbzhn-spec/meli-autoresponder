import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

def search_listings(query):
    url=f"https://api.mercadolibre.com/sites/MLM/search?q={urllib.parse.quote(query)}&category=MLM59800&limit=50"
    r=requests.get(url,headers=H).json()
    return r.get("results",[])

# Aggregate by catalog_product_id and total sold across active winners
def find_top_cpid(query, color_keys):
    print(f"\n=== {query} ===")
    res=search_listings(query)
    # Filter for catalog listings AND title mentions the color
    cpid_data={}  # cpid -> {"title":..,"sold":sum, "price_min":min, "n":count}
    for it in res:
        t=(it.get("title") or "").lower()
        if not any(ck in t for ck in color_keys): continue
        cpid=it.get("catalog_product_id")
        if not cpid: continue
        sold=it.get("sold_quantity",0) or 0
        cpid_data.setdefault(cpid,{"title":it.get("title"),"sold":0,"price_min":9999999,"n":0,"sample_iid":it.get("id")})
        cpid_data[cpid]["sold"]+=sold
        cpid_data[cpid]["price_min"]=min(cpid_data[cpid]["price_min"],it.get("price") or 9999999)
        cpid_data[cpid]["n"]+=1
    # also try to query /products to get total catalog sold
    ranked=sorted(cpid_data.items(),key=lambda x:-x[1]["sold"])
    for cpid,info in ranked[:8]:
        # get product info
        try:
            p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
            name=p.get("name","")
            attrs={a["id"]:a.get("value_name") for a in (p.get("attributes") or [])}
        except Exception:
            name=info["title"]; attrs={}
        print(f"CPID={cpid} sold_in_listings={info['sold']} min_price=${info['price_min']} listings_found={info['n']}")
        print(f"  name={name}")
        print(f"  color_attr={attrs.get('COLOR')} model={attrs.get('MODEL')}")
        print(f"  sample_listing=MLM{info['sample_iid'][-9:] if info['sample_iid'] else '?'}")
    return ranked

# Clip 5 Camuflaje
find_top_cpid("jbl clip 5 camuflaje",["camuflaje","camuflado"])
# Clip 5 Celeste con rosado / Squad
find_top_cpid("jbl clip 5 celeste rosa",["celeste","squad","azul","rosa"])
