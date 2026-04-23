import os,requests,json
# Probar las 3 cuentas y listar claims
ACCOUNTS={
    "Juan":os.environ["MELI_REFRESH_TOKEN"],
    "Claribel":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"],
    "ASVA":os.environ["MELI_REFRESH_TOKEN_ASVA"],
    "Raymundo":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],
}
TARGET="2000012579902645"

for name,rt in ACCOUNTS.items():
    try:
        r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
        H={"Authorization":f"Bearer {r['access_token']}"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
        print(f"\n=== {name} ({me.get('nickname')} {me.get('id')}) ===")
        # GET directo
        g=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{TARGET}",headers=H,timeout=10)
        print(f"  GET claim {TARGET}: {g.status_code}")
        if g.status_code==200:
            print(f"    ENCONTRADO! {json.dumps(g.json(),ensure_ascii=False)[:800]}")
        # Listar abiertos
        for q in ["?status=opened","?stage=claim","?stage=dispute",""]:
            l=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/search{q}",headers=H,timeout=10)
            if l.status_code==200:
                data=l.json().get("data") or []
                print(f"  search{q}: total={l.json().get('paging',{}).get('total',0)} first5:")
                for c in data[:5]:
                    print(f"    id={c.get('id')} stage={c.get('stage')} status={c.get('status')} reason={c.get('reason_id')} res={c.get('resource_id')}")
                if data: break
    except Exception as e:
        print(f"  ERR {name}: {e}")
