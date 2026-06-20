import os, requests
API="https://api.mercadolibre.com"
def sec(t): print(f"\n=== {t} ===")

# 1) intentar token Adrian (refresh local primero)
sec("Token ADRIAN")
RT = os.environ.get("MELI_REFRESH_TOKEN_ADRIAN")
if not RT:
    print("ENV MELI_REFRESH_TOKEN_ADRIAN no existe. Probando otros nombres...")
    for k in os.environ:
        if "ADRIAN" in k.upper() or "ADRI" in k.upper():
            print("  encontrado env:", k)
else:
    print("MELI_REFRESH_TOKEN_ADRIAN presente, len:", len(RT))
    r=requests.post(f"{API}/oauth/token", data={
        "grant_type":"refresh_token",
        "client_id":os.environ.get("MELI_APP_ID",""),
        "client_secret":os.environ.get("MELI_APP_SECRET",""),
        "refresh_token":RT,
    }, timeout=20)
    print("  refresh local status:",r.status_code, r.text[:200])
    if r.status_code==200:
        AT=r.json().get("access_token")
        if AT:
            H={"Authorization":f"Bearer {AT}"}
            me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
            print("  Adrian uid:",me.get("id"),"nick:",me.get("nickname"))
            sec("domain_discovery aceites esenciales")
            for q in ["aceite esencial","aceites esenciales aromaterapia","aceite esencial difusor","esencias aromaticas","aceite aromatico"]:
                rr=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"q":q,"limit":4},headers=H,timeout=15)
                print(f"q='{q}'")
                try:
                    for d in rr.json(): print(f"  {d.get('domain_id')} | {d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
                except: print("  err")
