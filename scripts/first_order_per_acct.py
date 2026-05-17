import os,requests,json
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    if not rt: return None
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
    return r.get("access_token")
ACCOUNTS=[("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),("Juan","MELI_REFRESH_TOKEN_JUAN"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),("Asva","MELI_REFRESH_TOKEN_ASVA"),("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),("Bren","MELI_REFRESH_TOKEN_BREN")]
for name,env in ACCOUNTS:
    T=tok(os.environ.get(env,""))
    if not T: 
        print(f"{name}: NO_TOKEN"); continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me.get("id")
    if not uid: 
        print(f"{name}: NO_UID"); continue
    # Ascending order by date_created — first = earliest
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&sort=date_asc&limit=1",headers=H).json()
    results=r.get("results",[])
    total=r.get("paging",{}).get("total",0)
    first=results[0].get("date_created","?")[:10] if results else "?"
    print(f"{name:<10} uid={uid:>12} total_orders={total:>6} first={first}")
