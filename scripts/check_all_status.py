"""Revisar status actual de TODAS las catalog_suggestions creadas en esta sesión y previas."""
import os, sys, requests, json
sys.path.insert(0, "scripts")
import meli_token
API="https://api.mercadolibre.com"

# (sid, etiqueta, account_owner)
SUGGESTIONS = [
    # Adrian (Piedra Viva)
    ("MLM3034199669", "PV aceites esenciales", "ADRIAN"),
    ("MLM3034200499", "PV esotéricos (título limpio)", "ADRIAN"),

    # ASVA Piedra Viva en MLM-PERFUMES (sesiones previas)
    ("MLM2967890523", "PV V1 Especiados", "ASVA"),
    ("MLM5448695704", "PV V2 Amaderado", "ASVA"),
    ("MLM5486087822", "PV V3 Amaderado", "ASVA"),
    ("MLM2999620497", "PV V4 Especiados", "ASVA"),

    # ASVA Flofen
    ("MLM5406965296", "Flofen V1 Gourmand", "ASVA"),
    ("MLM5448605608", "Flofen V2 Orientales", "ASVA"),
    ("MLM5486087672", "Flofen V3 Gourmand", "ASVA"),

    # ASVA speakers / audífonos
    ("MLM5395078912", "Buds 2 audífonos", "ASVA"),
    ("MLM5400602020", "Flipi7 Rojo", "ASVA"),
    ("MLM5398447738", "Flipi7 Azul", "ASVA"),
    ("MLM5400602058", "Flipi7 Morado", "ASVA"),
    ("MLM5398447740", "Flipi7 Negro", "ASVA"),

    # Batch 12 TAL esotéricos (HOY)
    ("MLM3034230563", "Corazón de Copal", "MAYRELY"),
    ("MLM5545611120", "Sombra del Jaguar", "MAYRELY"),
    ("MLM5545598222", "Mandarin Quetzal", "WILBERT"),
    ("MLM5545598280", "Tláloc Intenso", "WILBERT"),
    ("MLM3034230787", "Cenote Azul", "CLARIBEL"),
    ("MLM5545598338", "Quinto Aliento", "CLARIBEL"),
    ("MLM5545611344", "Xibalbá Royal", "RAYMUNDO"),
    ("MLM5545588486", "Fuerza de Kukulcán", "RAYMUNDO"),
    ("MLM3034230895", "Manantial del Valle Real", "ASGARI"),
    ("MLM5545598456", "Flor de la Noche", "ASGARI"),
    ("MLM3034230967", "Luz del Desierto", "JUAN"),
    ("MLM5545598502", "Rosa del Viento", "JUAN"),
]

WORKER = {"WILBERT","YC_NEW","JUAN","RAYMUNDO","CLARIBEL","ASVA","BREN"}
TOKEN_CACHE = {}
def at_for(account):
    if account in TOKEN_CACHE: return TOKEN_CACHE[account]
    if account in WORKER:
        at = meli_token.get_access_token(account)
    else:
        env = f"MELI_REFRESH_TOKEN_{account}"
        rt = os.environ.get(env)
        if not rt: raise RuntimeError(f"no env {env}")
        at = meli_token.refresh(rt)["access_token"]
    TOKEN_CACHE[account] = at
    return at

bystatus = {}
rows = []
for sid, label, account in SUGGESTIONS:
    try:
        AT = at_for(account)
    except Exception as e:
        rows.append((sid,label,account,f"TOKEN_FAIL:{e}","")); continue
    H={"Authorization":f"Bearer {AT}"}
    r = requests.get(f"{API}/catalog_suggestions/{sid}", headers=H, timeout=20)
    if r.status_code != 200:
        rows.append((sid,label,account,f"HTTP{r.status_code}",r.text[:120])); continue
    d = r.json()
    status = d.get("status","?")
    cpid = d.get("catalog_product_id","")
    reasons = d.get("rejected_reasons") or []
    rmsg = "; ".join([rr.get("description") or rr.get("name") or "" for rr in reasons])[:160]
    rows.append((sid,label,account,status,cpid or rmsg))
    bystatus.setdefault(status,0)
    bystatus[status]+=1

print("\n=== STATUS BREAKDOWN ===")
for s,n in sorted(bystatus.items(), key=lambda x:-x[1]):
    print(f"  {s}: {n}")

print("\n=== DETALLE ===")
for sid,label,acc,st,extra in rows:
    print(f"  [{st:14s}] {sid:14s} {acc:8s} | {label:32s} | {extra}")
