import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

# Site search with catalog_listing filter, get sold from individual listings
def site_search(q):
    url=f"https://api.mercadolibre.com/sites/MLM/search?q={urllib.parse.quote(q)}&category=MLM59800&limit=50"
    r=requests.get(url,headers=H).json()
    return r.get("results",[])

# Aggregate by cpid sold across listings
def best_cpid_for(query,color_keys):
    print(f"\n========== {query} ==========")
    listings=site_search(query)
    cpid_data={}
    for it in listings:
        cpid=it.get("catalog_product_id")
        if not cpid: continue
        title=(it.get("title") or "")
        tl=title.lower()
        if "clip 5" not in tl and "clip5" not in tl: continue
        # color must match
        if not any(ck in tl for ck in color_keys): continue
        sold=it.get("sold_quantity",0) or 0
        d=cpid_data.setdefault(cpid,{"sold":0,"n":0,"sample_title":title,"min_price":99999,"sample_iid":it.get("id"),"thumb":it.get("thumbnail")})
        d["sold"]+=sold; d["n"]+=1
        d["min_price"]=min(d["min_price"], it.get("price") or 99999)
    ranked=sorted(cpid_data.items(),key=lambda x:-x[1]["sold"])[:8]
    for cpid,d in ranked:
        # fetch product info
        pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
        attrs={a.get("id"):a.get("value_name") for a in (pd.get("attributes") or [])}
        bbw=pd.get("buy_box_winner") or {}
        pics=pd.get("pictures") or []
        pic_url=pics[0].get("url") if pics else None
        print(f"\nCPID={cpid}")
        print(f"  product_name={pd.get('name','')}")
        print(f"  COLOR={attrs.get('COLOR')}  MODEL={attrs.get('MODEL')}")
        print(f"  sold_via_listings={d['sold']} listings_count={d['n']}")
        print(f"  bbw_price=${bbw.get('price')} bbw_seller={bbw.get('seller_id')}")
        print(f"  link=https://articulo.mercadolibre.com.mx/p/{cpid}")
        if pic_url: print(f"  pic={pic_url}")

# CAMUFLAJE
for q in ["jbl clip 5 camuflaje","jbl clip 5 squad","jbl clip 5 camuflada","jbl clip 5 camo"]:
    best_cpid_for(q,["camuflaj","camuflad","squad","camo","verde musg"])

# CELESTE+ROSA
for q in ["jbl clip 5 celeste rosa","jbl clip 5 azul rosa","jbl clip 5 azul cielo rosa","jbl clip 5 celeste","jbl clip 5 cielo"]:
    best_cpid_for(q,["celeste","cielo","azul claro","rosa","pink","sky","celest"])
