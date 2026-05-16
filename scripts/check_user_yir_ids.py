import os,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
USER_STOCK={
  "MLM2935286605":9,
  "MLM2935286537":40,
  "MLM2935286615":10,
  "MLM2935286651":40,
  "MLM2935286681":10,
  "MLM2935286703":10,
  "MLM2935298361":12,
  "MLM2935286669":11,
  "MLM2935286557":3,
  "MLM2935286629":11,
  "MLM5353056250":12,
  "MLM5353056406":12,
}
for iid,qty in USER_STOCK.items():
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    print(f"{iid} real={qty:>3} st={g.get('status'):<8} sub={g.get('sub_status')} visible={g.get('available_quantity')} ${g.get('price')} '{(g.get('title') or '')[:50]}'")
