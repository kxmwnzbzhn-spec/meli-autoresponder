import os,requests,json,base64
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
repo="kxmwnzbzhn-spec/meli-autoresponder"

# Initial user stock counts (lo que ME PROPORCIONÓ)
USER_STOCK={
  "MLM2935286605":9,"MLM2935286537":40,"MLM2935286615":10,"MLM2935286651":40,
  "MLM2935286681":10,"MLM2935286703":10,"MLM2935298361":12,"MLM5353104620":11,
  "MLM2935286557":3,"MLM2935286629":11,"MLM5353056250":12,"MLM5353056406":12,
}
NAMES={"MLM2935286605":"Angel Nova","MLM2935286537":"Billie Eilish","MLM2935286615":"Jo Milano Spades","MLM2935286651":"Million Gold H","MLM2935286681":"Lattafa Khamrah","MLM2935286703":"Creed Aventus","MLM2935298361":"Dior Sauvage","MLM5353104620":"Orientica Royal Amber","MLM2935286557":"Lattafa Confession","MLM2935286629":"Orientica Amber Rouge","MLM5353056250":"Armaf Island Bliss","MLM5353056406":"Lady Million Gold"}

cfg={"_meta":{"description":"Yiriam stock real almacén - 12 perfumes","updated":"2026-05-16","total":sum(USER_STOCK.values())}}
for iid,real in USER_STOCK.items():
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=sold_quantity",headers=H).json()
    sold=int(g.get("sold_quantity",0) or 0)
    cfg[iid]={"title":NAMES[iid],"real_stock":real,"master_stock":real,"min_visible":1,"available_quantity":1,"auto_replenish":True,"active":True,"last_sold":sold}
    print(f"{iid} '{NAMES[iid]}' real={real} baseline_sold={sold}")

new_b64=base64.b64encode(json.dumps(cfg,indent=2).encode()).decode()
sha_resp=requests.get(f"https://api.github.com/repos/{repo}/contents/stock_config_yiriam.json",headers={"Authorization":f"Bearer {GHT}"}).json()
u=requests.put(f"https://api.github.com/repos/{repo}/contents/stock_config_yiriam.json",
    headers={"Authorization":f"Bearer {GHT}","Content-Type":"application/json"},
    json={"message":"seed baseline last_sold","content":new_b64,"sha":sha_resp.get("sha")})
print(f"\ncfg commit http={u.status_code}")
