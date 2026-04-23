import os,requests,json,time
def get_token(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()["access_token"]

TARGETS=[
    ("JUAN","MLM2883448187",os.environ["MELI_REFRESH_TOKEN"]),
    ("RAYMUNDO","MLM5235542250",os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]),
]

for label,iid,rt in TARGETS:
    print(f"\n=== {label} {iid} ===")
    AT=get_token(rt)
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    cur=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=variations,price,available_quantity",headers=H).json()
    vars=cur.get("variations") or []
    print(f"  variants actuales: {len(vars)}")
    
    new_vars=[]
    for v in vars:
        vid=v.get("id")
        color=None
        for ac in (v.get("attribute_combinations") or []):
            if ac.get("id")=="COLOR": color=ac.get("value_name"); break
        new_vars.append({
            "id":vid,
            "price":599,
            "available_quantity":10,
            "attribute_combinations":v.get("attribute_combinations",[]),
            "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
        })
        print(f"    {color} id={vid} -> $599 x10u")
    
    body={"variations":new_vars}
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=30)
    print(f"  update: {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"    err: {rp.text[:500]}")
    time.sleep(2)
