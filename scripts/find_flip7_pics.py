import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
for q in ["jbl flip 7 morado","jbl flip 7 purple","jbl flip 7 violeta","jbl flip 7 púrpura"]:
    print(f"\n--- {q} ---")
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(q)}&limit=15"
    r=requests.get(url,headers=H).json()
    for p in r.get("results",[])[:8]:
        name=p.get("name","")
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        col=attrs.get("COLOR","")
        if "flip 7" in name.lower() and any(k in (name+col).lower() for k in ["morad","purp","violet","púrp"]):
            pd=requests.get(f"https://api.mercadolibre.com/products/{p.get('id')}",headers=H).json()
            pics=[(pp.get("url") or pp.get("secure_url")) for pp in (pd.get("pictures") or [])][:5]
            print(f"  CPID={p.get('id')} color={col} name={name[:60]} pics={len(pics)}")
            if pics: print(f"  pic1={pics[0]}")
