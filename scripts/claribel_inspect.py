import os,requests,json
rc=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
H={"Authorization":f"Bearer {rc['access_token']}"}
for iid in ["MLM5226013726","MLM5226014888"]:
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H).json()
    print(f"\n=== {iid} ===")
    for a in (d.get("attributes") or []):
        if a.get("id") in ("GTIN","OLFACTORY_FAMILIES","BRAND","IS_HIGHLIGHT_BRAND","IS_TOM_BRAND"):
            print(f"  {a.get('id')}: id={a.get('value_id')} name='{a.get('value_name')}' values={a.get('values')}")
