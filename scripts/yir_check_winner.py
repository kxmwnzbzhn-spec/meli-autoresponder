import os,json,requests
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
TY=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT_Y}).json()["access_token"]
HY={"Authorization":f"Bearer {TY}"}
items=["MLM5291785036","MLM5291788562","MLM2923681279"]
for iid in items:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,status,sub_status,catalog_product_id,catalog_listing",headers=HY).json()
    p=requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",headers=HY).json()
    print(json.dumps({"id":iid,"price":g.get("price"),"st":g.get("status"),"sub":g.get("sub_status"),"cpid":g.get("catalog_product_id"),"cat_listing":g.get("catalog_listing"),"ptw":p.get("price_to_win") or p.get("price"),"status":p.get("status"),"current_price":p.get("current_price")},ensure_ascii=False))
