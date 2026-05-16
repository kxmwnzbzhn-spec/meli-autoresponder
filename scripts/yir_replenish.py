#!/usr/bin/env python3
"""Yir replenish — respeta stock_config_yiriam.json real_stock."""
import os,requests,time,json,base64

RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ.get("GH_TOKEN","")
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Load stock_config_yiriam.json from repo
repo="kxmwnzbzhn-spec/meli-autoresponder"
GHH={"Authorization":f"Bearer {GHT}"} if GHT else {}
cfg_resp=requests.get(f"https://api.github.com/repos/{repo}/contents/stock_config_yiriam.json",headers=GHH).json()
cfg={}
if "content" in cfg_resp:
    cfg=json.loads(base64.b64decode(cfg_resp["content"]))
else:
    print("WARN no stock_config_yiriam.json, using empty")

actions=[]
for iid,c in cfg.items():
    if iid.startswith("_"): continue
    real=int(c.get("real_stock",0) or 0)
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    st=g.get("status"); sub=g.get("sub_status",[]); qty=g.get("available_quantity",0)
    sold=int(g.get("sold_quantity",0) or 0)
    last_sold=int(c.get("last_sold",0) or 0)
    delta=sold-last_sold
    # If item sold since last check, decrement real
    if delta>0 and real>0:
        real=max(real-delta,0)
        c["real_stock"]=real
        c["last_sold"]=sold
        actions.append(f"DECR {iid}: sold +{delta} → real={real}")
    elif delta>0:
        c["last_sold"]=sold
    
    # Replenish if paused with stock
    if st=="paused" and real>0:
        # Set qty=1 then active
        r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
        time.sleep(0.4)
        r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        actions.append(f"REPL {iid} '{(g.get('title') or '')[:30]}' real={real} qty=1 active http={r2.status_code}")
        time.sleep(0.3)
    elif st=="paused" and real<=0:
        actions.append(f"AGOTADO {iid} — no replenish")
    elif st=="closed":
        actions.append(f"CLOSED {iid} — manual relist needed")

# Commit updated config
if cfg and GHT and "sha" in cfg_resp:
    new_b64=base64.b64encode(json.dumps(cfg,indent=2).encode()).decode()
    u=requests.put(f"https://api.github.com/repos/{repo}/contents/stock_config_yiriam.json",headers={"Authorization":f"Bearer {GHT}","Content-Type":"application/json"},json={"message":"yir replenish auto update","content":new_b64,"sha":cfg_resp["sha"]})
    actions.append(f"cfg commit http={u.status_code}")

print(f"yir_replenish: {len(actions)} acciones")
for a in actions: print(f"  {a}")
