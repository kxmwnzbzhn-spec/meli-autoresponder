"""Probe catalog_suggestions API de MELI para todas las cuentas."""
import os, requests, json
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCS = {
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
}

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

# Probar cada endpoint reportado
for acc, rt in ACCS.items():
    if not rt: continue
    print(f"\n{'='*70}\n=== {acc} ===")
    at=tok(rt)
    if not at:
        print("  no token")
        continue
    H={"Authorization":f"Bearer {at}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
    uid=me.get("id")
    print(f"  uid={uid} nick={me.get('nickname')}")

    # 1) Eligibilidad y cuota del usuario
    print(f"\n  --- /catalog_suggestions/users/{uid} (eligibility) ---")
    try:
        r=requests.get(f"https://api.mercadolibre.com/catalog_suggestions/users/{uid}",headers=H,timeout=10)
        print(f"    {r.status_code}: {r.text[:500]}")
    except Exception as e:
        print(f"    err: {e}")

    # 2) Dominios disponibles
    print(f"\n  --- /catalog_suggestions/sites/MLM/domains ---")
    try:
        r=requests.get("https://api.mercadolibre.com/catalog_suggestions/sites/MLM/domains",headers=H,timeout=10)
        print(f"    {r.status_code}: {r.text[:600]}")
    except Exception as e:
        print(f"    err: {e}")

    # 3) Listar suggestions del usuario
    print(f"\n  --- /catalog_suggestions/search?seller_id={uid} ---")
    try:
        r=requests.get(f"https://api.mercadolibre.com/catalog_suggestions/search?seller_id={uid}",headers=H,timeout=10)
        print(f"    {r.status_code}: {r.text[:500]}")
    except Exception as e:
        print(f"    err: {e}")

    # Solo probar Raymundo en detalle (ya alcanza para ver el patron)
    if acc != "Raymundo": continue

    # 4) Topic notifications
    print(f"\n  --- /catalog_suggestions topic info ---")
    try:
        r=requests.get(f"https://api.mercadolibre.com/users/{uid}/applications",headers=H,timeout=10)
        print(f"    apps: {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"    err: {e}")

    # 5) Brand-central api?
    print(f"\n  --- /brand-central/sites/MLM ---")
    try:
        r=requests.get("https://api.mercadolibre.com/brand-central/sites/MLM",headers=H,timeout=10)
        print(f"    {r.status_code}: {r.text[:500]}")
    except Exception as e:
        print(f"    err: {e}")
