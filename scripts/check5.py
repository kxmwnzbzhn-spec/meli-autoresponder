import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
IDS=["MLM2880754185","MLM2880758743","MLM2880766045","MLM2880754229","MLM5222983148","MLM2880762615"]
res=requests.get(f"https://api.mercadolibre.com/items?ids={','.join(IDS)}&attributes=id,title,status,sub_status,price",headers=H).json()
for x in res:
    b=x.get("body",{})
    print(f"{b.get('id')} | {b.get('status')}/{b.get('sub_status')} | ${b.get('price')} | {b.get('title')}")
