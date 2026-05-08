import os, json, time, requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]
CS=os.environ["MELI_APP_SECRET"]
def tok():
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()
    return r["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

TARGETS={
  549:["MLM2910457917","MLM2910880717","MLM2910806817"],
  449:["MLM2910806845","MLM2910768333","MLM2910806881"],
  799:["MLM2910880769","MLM2910806871","MLM2910768361","MLM2910806853","MLM2910457991","MLM2910457983","MLM2910457973"],
  899:["MLM5295549238","MLM5295460002"],
}

results=[]
for target,items in TARGETS.items():
  for iid in items:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,price,original_price,title,status",headers=H).json()
    cur=g.get("price")
    title=g.get("title","")[:50]
    st=g.get("status")
    # Need original_price > price to show discount. If current already at/below target, just set price.
    op = max(int(cur or target), int(target*1.4))
    if op <= target: op = int(target*1.4)
    body={"price":target,"original_price":op}
    p=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body)
    results.append({"item":iid,"target":target,"prev":cur,"new":target,"orig":op,"http":p.status_code,"title":title,"status":st,"err":(p.json().get("message") if p.status_code>=400 else None)})
    print(f"{iid} target=${target} prev=${cur} -> ${target} orig=${op} http={p.status_code}")
    time.sleep(0.5)

# Update stock_config to lock floor
import subprocess
sc_url=f"https://api.github.com/repos/{os.environ['REPO_OWNER']}/meli-autoresponder/contents/scripts/stock_config_wilbert.json"
import base64
g=requests.get(sc_url,headers={"Authorization":f"Bearer {os.environ['GH_TOKEN']}"}).json()
cfg=json.loads(base64.b64decode(g["content"]))
for target,items in TARGETS.items():
  for iid in items:
    cfg.setdefault(iid,{})
    cfg[iid]["floor_price"]=target
    cfg[iid]["ceiling_price"]=target
    cfg[iid]["floor_locked_by_user"]=True
new_b64=base64.b64encode(json.dumps(cfg,indent=2).encode()).decode()
r=requests.put(sc_url,headers={"Authorization":f"Bearer {os.environ['GH_TOKEN']}","Content-Type":"application/json"},json={"message":"Lock promo prices 549/449/799/899","content":new_b64,"sha":g["sha"]})
print("config update:",r.status_code)

print(json.dumps(results,indent=2))
