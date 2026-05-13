import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

def find_top(query):
    print(f"\n========== {query} ==========")
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(query)}&limit=30"
    r=requests.get(url,headers=H).json()
    results=r.get("results",[])
    for p in results:
        cpid=p.get("id")
        name=p.get("name","")
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        color=attrs.get("COLOR","") or attrs.get("MAIN_COLOR","")
        model=attrs.get("MODEL","")
        # filter just clip 5
        nl=name.lower()
        if "clip 5" not in nl and "clip5" not in nl: continue
        print(f"  CPID={cpid}  COLOR={color}  MODEL={model}")
        print(f"     name={name}")

# Camuflaje keywords
for q in ["jbl clip 5 squad","jbl clip 5 camo","jbl clip 5 camuflado","jbl clip 5 militar"]:
    find_top(q)

# Celeste/Rosa keywords
for q in ["jbl clip 5 dia y noche","jbl clip 5 day night","jbl clip 5 sunset","jbl clip 5 amanecer","jbl clip 5 celeste","jbl clip 5 azul claro"]:
    find_top(q)
