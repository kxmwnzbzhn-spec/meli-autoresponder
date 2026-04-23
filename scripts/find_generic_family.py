import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
# Revisa children de catalogos genericos
for cid in ["MLM29772333","MLM47809508","MLM61316998"]:
    d=requests.get(f"https://api.mercadolibre.com/products/{cid}",headers=H).json()
    kids=(d.get("children_ids") or [])
    print(f"=== {cid}: {d.get('name','')[:50]} ===")
    for k in kids[:10]:
        dc=requests.get(f"https://api.mercadolibre.com/products/{k}",headers=H).json()
        color=None
        for a in (dc.get("attributes") or []):
            if a.get("id")=="COLOR":
                color=a.get("value_name")
                break
        print(f"  {k}: {dc.get('name','')[:40]} | COLOR={color}")
