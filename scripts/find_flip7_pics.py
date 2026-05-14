import os,json,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}

# Search for Flip 7 catalogs (color-specific) to grab pics
COLORS=["negro","morado","azul","rojo"]
result={}
for col in COLORS:
    q=f"jbl flip 7 {col}"
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(q)}&limit=10"
    r=requests.get(url,headers=H).json()
    for p in r.get("results",[]):
        name=(p.get("name") or "").lower()
        if "flip 7" not in name and "flip7" not in name: continue
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        prod_color=(attrs.get("COLOR") or "").lower()
        if col not in name.lower() and col not in prod_color: continue
        pd=requests.get(f"https://api.mercadolibre.com/products/{p.get('id')}",headers=H).json()
        pics=[(pp.get("url") or pp.get("secure_url")) for pp in (pd.get("pictures") or [])][:5]
        if pics:
            result[col]={"cpid":p.get("id"),"name":p.get("name"),"color":prod_color,"pics":pics}
            print(f"{col.upper()}: cpid={p.get('id')} pics={len(pics)} sample={pics[0]}")
            break
print("\n=== RESULT ===")
print(json.dumps(result,indent=2,ensure_ascii=False))
