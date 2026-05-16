import os,json,requests,base64
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
GHT=os.environ["GH_TOKEN"]
WB=["MLM5265893750","MLM5309659262","MLM2908793361","MLM2916649417","MLM2916897121","MLM2908818183","MLM2916908777","MLM2916672247","MLM2916676513","MLM2916908753","MLM2916921559","MLM2916700919"]
g=requests.get(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/contents/stock_config_wilbert.json",headers={"Authorization":f"Bearer {GHT}"}).json()
cfg=json.loads(base64.b64decode(g["content"]))
for iid in WB:
    info=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,title",headers=H).json()
    p=info.get("price")
    if p is None: continue
    cfg.setdefault(iid,{})
    cfg[iid]["floor_price"]=int(p)
    cfg[iid]["ceiling_price"]=int(p)
    cfg[iid]["floor_locked_by_user"]=True
    print(f"  {iid} locked at ${p}")
new=base64.b64encode(json.dumps(cfg,indent=2).encode()).decode()
u=requests.put(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/contents/stock_config_wilbert.json",headers={"Authorization":f"Bearer {GHT}","Content-Type":"application/json"},json={"message":"Lock 12 Wilbert floors (Yiriam ganando)","content":new,"sha":g["sha"]})
print("cfg commit:",u.status_code)
