import os,requests,base64,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
ids=[]; off=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H).json()
    res=r.get("results",[])
    if not res: break
    ids+=res; off+=100
    if off>=r.get("paging",{}).get("total",0): break
print(f"PAUSANDO de nuevo: {len(ids)} items")
ok=0
for iid in ids:
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300: ok+=1
print(f"✓ pausados {ok}/{len(ids)}")
# Reset state idempotent
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
s=requests.get(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/contents/inventory/yiriam_reactivate_state.json",headers=GHH).json()
new_state={"last_run":None,"_note":"reset por dry-run accidental, listo para cron 6am Mérida"}
new_b64=base64.b64encode(json.dumps(new_state,indent=2,ensure_ascii=False).encode()).decode()
requests.put(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/contents/inventory/yiriam_reactivate_state.json",headers={**GHH,"Content-Type":"application/json"},json={"message":"reset state","content":new_b64,"sha":s.get("sha")})
print("state reset OK")
# Disable war again
wfr=requests.put(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/actions/workflows/277666461/disable",headers=GHH)
print(f"war wf disable http={wfr.status_code}")
