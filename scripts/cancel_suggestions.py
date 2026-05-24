import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
IDS=["MLM5395078678","MLM5396839552"]   # las 2 CREATION erróneas
for sid in IDS:
    print(f"\n=== {sid} ===")
    rd=requests.delete(f"{API}/catalog_suggestions/{sid}",headers=H,timeout=30)
    print(f"  DELETE -> {rd.status_code} {rd.text[:160]}")
    if rd.status_code not in (200,204):
        # intentar marcar CANCELLED via PUT
        for st in ("CANCELLED","CANCELED","REJECTED"):
            rp=requests.put(f"{API}/catalog_suggestions/{sid}",headers=HJ,json={"status":st},timeout=30)
            print(f"  PUT status={st} -> {rp.status_code} {rp.text[:120]}")
            if rp.status_code<300: break
    # confirmar estado actual
    g=requests.get(f"{API}/catalog_suggestions/{sid}",headers=H,timeout=20)
    try: print(f"  now status={g.json().get('status')}")
    except: print(f"  GET {g.status_code} {g.text[:100]}")
print("DONE")
