import os, requests
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASGARI":   os.environ.get("MELI_REFRESH_TOKEN_ASGARI"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
}
print(f"{'Cuenta':<10} {'IID':<16} {'Stock':<7} {'Sold':<6} {'Status':<10} Title")
for acc, rt in ACCS.items():
    if not rt: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    at=r.get("access_token")
    if not at: continue
    H={"Authorization":f"Bearer {at}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me["id"]
    # Buscar items con mandarin
    iids=[]
    for st in ["active","paused"]:
        offset=0
        while True:
            rr=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=20).json()
            for iid in rr.get("results",[]): iids.append(iid)
            offset+=50
            if offset>=rr.get("paging",{}).get("total",0): break
    # Get items en chunks
    for i in range(0,len(iids),20):
        chunk=iids[i:i+20]
        rr=requests.get("https://api.mercadolibre.com/items",headers=H,params={"ids":",".join(chunk),"attributes":"id,title,available_quantity,sold_quantity,status"},timeout=20).json()
        for resp in rr:
            if resp.get("code")!=200: continue
            it=resp["body"]
            title=(it.get("title","") or "").lower()
            if "mandarin" in title:
                print(f"{acc:<10} {it['id']:<16} {it.get('available_quantity',0):<7} {it.get('sold_quantity',0):<6} {it.get('status',''):<10} {it.get('title','')[:60]}")
