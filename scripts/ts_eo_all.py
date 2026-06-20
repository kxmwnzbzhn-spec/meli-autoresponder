import os, json, requests
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
r=requests.get(f"{API}/domains/MLM-ESSENTIAL_OILS/technical_specs",headers=H,timeout=20)
print("status",r.status_code)
seen=set()
def tags_of(n):
    t=n.get("tags")
    return ([k for k,v in t.items() if v] if isinstance(t,dict) else (t if isinstance(t,list) else []))
def walk(n):
    if isinstance(n,dict):
        if n.get("id") and ("tags" in n or "values" in n or "value_type" in n):
            aid=n.get("id")
            if aid not in seen:
                seen.add(aid)
                tg=tags_of(n)
                print(f"[{aid}] {n.get('name')} tg={tg}")
        for v in n.values(): walk(v)
    elif isinstance(n,list):
        for v in n: walk(v)
walk(r.json())
