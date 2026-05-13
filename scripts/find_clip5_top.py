import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

def get_sold(cpid):
    # Try multiple ways to get sold
    try:
        # sum sold_quantity from /products/{cpid}/items winners
        r=requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=50",headers=H).json()
        total=0; winners=0
        for it in r.get("results",[]):
            total += it.get("sold_quantity",0) or 0
            winners+=1
        return total, winners, r.get("paging",{}).get("total",0)
    except: return 0,0,0

# CAMO/CAMUFLAJE candidates
camo_cpids=[
  ("MLM48157832","Squad"),
  ("MLM44712057","Camuflada"),
  ("MLM58616124","Verde musgo"),
  ("MLM48364450","Camo"),
  ("MLM47219000","Verde musgo Jbl"),
]
print("\n=== CAMUFLAJE candidates ===")
for cpid,color in camo_cpids:
    s,w,tot=get_sold(cpid)
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    name=pd.get("name","")
    bbw=pd.get("buy_box_winner") or {}
    print(f"CPID={cpid} COLOR={color} sold_in_winners={s} listings={tot} price_winner=${bbw.get('price')} ")
    print(f"  name={name}")
    pics=pd.get("pictures") or []
    if pics: print(f"  pic={pics[0].get('url')}")

# Search for celeste/pink combos
print("\n=== Search Celeste/Pink ===")
for q in ["jbl clip 5 day tripper","jbl clip 5 eco","jbl clip 5 sunset","jbl clip 5 rosa","jbl clip 5 sky"]:
    print(f"  --- query: {q}")
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(q)}&limit=15"
    r=requests.get(url,headers=H).json()
    for p in r.get("results",[]):
        name=p.get("name","")
        if "clip 5" not in name.lower() and "clip5" not in name.lower(): continue
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        color=attrs.get("COLOR","") or attrs.get("MAIN_COLOR","")
        if not any(k in (color+name).lower() for k in ["celeste","sky","day","rosa","pink","sunset","tripper","aqua","blue","azul claro","sherbet"]): continue
        print(f"    CPID={p.get('id')}  COLOR={color}  name={name}")
