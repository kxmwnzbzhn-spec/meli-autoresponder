import os, requests
API="https://api.mercadolibre.com"
SID="MLM2886030837"
TARGET_SELLER=1668713481  # discovered

candidates=["WILBERT","YC_NEW","JUAN","ASVA","BREN","MILDRED","DILCIE","MG20260424","CLARIBEL","RAYMUNDO","ANGEL","ADRIAN"]
def tok(rt):
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=20).json()

for c in candidates:
    sec=f"MELI_REFRESH_TOKEN_{c}"
    if sec not in os.environ: continue
    t=tok(os.environ[sec])
    if "access_token" not in t: continue
    H={"Authorization":f"Bearer {t['access_token']}"}
    me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
    print(f"  {c}: seller_id={me.get('id')} nick={me.get('nickname')}")
    if me.get("id")==TARGET_SELLER:
        print(f"\n>>> OWNER = {c}, new RT: {t.get('refresh_token')}")
        HJ={**H,"Content-Type":"application/json"}
        g=requests.get(f"{API}/items/{SID}",headers=H,timeout=20).json()
        print(f"BEFORE: status={g.get('status')} price={g.get('price')} qty={g.get('available_quantity')} title='{(g.get('title') or '')[:65]}'")
        r=requests.put(f"{API}/items/{SID}",headers=HJ,json={"price":199},timeout=30)
        print(f"PUT price=199: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
        g2=requests.get(f"{API}/items/{SID}",headers=H,timeout=20).json()
        print(f"AFTER: status={g2.get('status')} price={g2.get('price')}")
        break
else:
    print(f"No account in my secrets owns seller {TARGET_SELLER}")
