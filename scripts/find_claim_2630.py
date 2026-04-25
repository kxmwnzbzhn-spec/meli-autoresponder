import os,requests,json
ACCOUNTS={
    "JUAN":os.environ["MELI_REFRESH_TOKEN"],
    "CLARIBEL":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"],
    "ASVA":os.environ["MELI_REFRESH_TOKEN_ASVA"],
    "RAYMUNDO":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],
    "DILCIE":os.environ.get("MELI_REFRESH_TOKEN_DILCIE",""),
    "MILDRED":os.environ.get("MELI_REFRESH_TOKEN_MILDRED",""),
}
TARGET="2000012630082161"

for label,rt in ACCOUNTS.items():
    if not rt: continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r: continue
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    print(f"\n=== {label} ({me.get('nickname')}) ===")
    
    # Try as claim_id, order_id, pack_id
    for path in [f"/post-purchase/v1/claims/{TARGET}",f"/orders/{TARGET}"]:
        rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=10)
        if rp.status_code==200:
            d=rp.json()
            print(f"  HIT {path}")
            print(json.dumps(d,ensure_ascii=False)[:1500])
    # Search claims by resource
    for rt2 in ["order","pack"]:
        s=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search?resource={rt2}&resource_id={TARGET}",headers=H,timeout=10).json()
        for c in (s.get("data") or []):
            print(f"  CLAIM resource={rt2}: {c.get('id')} reason={c.get('reason_id')} stage={c.get('stage')}")
    # opened
    s=requests.get("https://api.mercadolibre.com/post-purchase/v1/claims/search?status=opened&limit=20",headers=H,timeout=10).json()
    for c in (s.get("data") or []):
        if str(c.get("resource_id"))==TARGET or TARGET in str(c.get("id",""))[:13]:
            print(f"  OPEN MATCH id={c.get('id')} res={c.get('resource_id')} reason={c.get('reason_id')} stage={c.get('stage')}")
