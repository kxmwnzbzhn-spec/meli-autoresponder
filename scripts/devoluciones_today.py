import os,requests,datetime as dt
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    if not rt: return None
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
    return r.get("access_token")

ACCOUNTS=[("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),("Juan","MELI_REFRESH_TOKEN_JUAN"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),("Asva","MELI_REFRESH_TOKEN_ASVA"),("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),("Bren","MELI_REFRESH_TOKEN_BREN")]

today=dt.date.today().isoformat()
date_from=f"{today}T00:00:00.000-06:00"
date_to=f"{today}T23:59:59.000-06:00"

total_returns=0
by_carrier={}
detail=[]

for name,env in ACCOUNTS:
    T=tok(os.environ.get(env,""))
    if not T: 
        print(f"  {name}: NO_TOKEN"); continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me.get("id")
    if not uid:
        print(f"  {name}: no uid"); continue
    # Method 1: claims con motivo de devolución HOY
    cl=requests.get(f"https://api.mercadolibre.com/post-purchase/v2/claims/search?stage=claim&status=opened&type=mediations&sort=date_created,desc&limit=50",
                    headers=H,timeout=20).json()
    n_claims=cl.get("paging",{}).get("total",0) if isinstance(cl,dict) else 0
    
    # Method 2: shipments con status returned/return_requested/in_return creados HOY
    # search orders today, check each shipping
    r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50",headers=H,timeout=15).json()
    
    # Use ultimately: shipments returned endpoint
    # GET /shipments/search?seller_id=XXX&shipping_status=returned&date_created.from=...
    sh=requests.get(f"https://api.mercadolibre.com/shipments/search?seller_id={uid}&shipping_status=returned&date_created.from={date_from}&date_created.to={date_to}&limit=50",
                    headers=H,timeout=20).json()
    if isinstance(sh,dict):
        n_ret=sh.get("paging",{}).get("total",0)
    else:
        n_ret=0
    if n_ret>0 or n_claims>0:
        print(f"  {name}: claims_opened={n_claims} shipments_returned_today={n_ret}")
    total_returns+=n_ret
    
    # detail por carrier
    for s in (sh.get("results",[]) if isinstance(sh,dict) else []):
        carrier=s.get("logistic",{}).get("type") or s.get("shipping_option",{}).get("name") or "MELI Envíos"
        by_carrier[carrier]=by_carrier.get(carrier,0)+1
        detail.append({"account":name,"shipment":s.get("id"),"carrier":carrier,"sub":s.get("substatus")})

print(f"\n=== Devoluciones HOY ({today}) ===")
print(f"Total devoluciones: {total_returns}")
print(f"Por carrier: {by_carrier}")
for d in detail[:10]: print(f"  {d}")
