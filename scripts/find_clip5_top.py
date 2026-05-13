import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

# Get info per cpid: name, color, bbw_price, n_listings, total_visits
def detail(cpid):
    p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
    bbw=p.get("buy_box_winner") or {}
    pics=p.get("pictures") or []
    pic=pics[0].get("url") if pics else None
    # try get total listings
    it=requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=1",headers=H).json()
    n_listings=it.get("paging",{}).get("total",0)
    return {"cpid":cpid,"name":p.get("name"),"color":attrs.get("COLOR"),"model":attrs.get("MODEL"),
            "bbw_price":bbw.get("price"),"bbw_seller":bbw.get("seller_id"),"n_listings":n_listings,
            "pic":pic,"link":f"https://articulo.mercadolibre.com.mx/p/{cpid}"}

CAMO=["MLM44712057","MLM58616124","MLM48157832","MLM48364450","MLM47219000"]
CELESTE=["MLM58592190","MLM40329314","MLM61825899","MLM37110751","MLM44714337","MLM63875183","MLM64288232","MLM35713227"]

print("\n==== CAMUFLAJE candidates ====")
for c in CAMO:
    d=detail(c)
    print(json.dumps(d,ensure_ascii=False))
print("\n==== AZUL / CELESTE / ROSA candidates ====")
for c in CELESTE:
    d=detail(c)
    print(json.dumps(d,ensure_ascii=False))
