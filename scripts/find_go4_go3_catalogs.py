#!/usr/bin/env python3
"""Busca catalog products de JBL Go 4 (todos colores) y JBL Go 3 (negra),
valida atributos, descarta los que tienen contradicciones título/BRAND/MODEL/COLOR.
Genera 2 listas: limpios + a descartar.
"""
import os, requests, json, time, re

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID, "client_secret": APP_SECRET, "refresh_token": RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}"}

def normalize(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

# Cargar publicados actuales
with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)
already = set()
for iid, meta in cfg.items():
    cpid = meta.get("catalog_product_id")
    if cpid:
        already.add(cpid)

queries_go4 = [
    "JBL Go 4", "Go4 JBL", "Bocina JBL Go 4", "Parlante JBL Go 4",
    "Altavoz JBL Go 4", "JBL audio Go 4",
]
queries_go3 = [
    "JBL Go 3 negro", "JBL Go3 negra", "Bocina JBL Go 3 Negro",
    "Altavoz JBL Go 3 negro",
]

found = {}  # cpid → {"name":..., "model":"Go 4"|"Go 3"}

def search_q(q, model):
    try:
        r = requests.get("https://api.mercadolibre.com/products/search",
                         headers=H, params={"status":"active","site_id":"MLM","q":q,"limit":50},
                         timeout=20)
        if r.status_code != 200: return
        for p in r.json().get("results", []):
            pid = p.get("id","")
            if not pid.startswith("MLM") or pid.startswith("MLMU"): continue
            name = (p.get("name") or "")
            nl = normalize(name)
            if model == "Go 4":
                if not (("go 4" in nl or "go4" in nl) and "jbl" in nl): continue
                if "go 3" in nl or "go3" in nl: continue  # excluir
            elif model == "Go 3":
                if not (("go 3" in nl or "go3" in nl) and "jbl" in nl): continue
                if "negr" not in nl and "black" not in nl: continue  # solo negro
            found[pid] = {"name": name[:80], "model": model}
    except Exception as e:
        print(f"err {q}: {e}")

print("=== Buscando Go 4 ===")
for q in queries_go4:
    search_q(q, "Go 4")
    time.sleep(0.5)
print(f"  Go 4 encontrados: {sum(1 for v in found.values() if v['model']=='Go 4')}")

print("\n=== Buscando Go 3 Negro ===")
for q in queries_go3:
    search_q(q, "Go 3")
    time.sleep(0.5)
print(f"  Go 3 negro encontrados: {sum(1 for v in found.values() if v['model']=='Go 3')}")

# Validar contradicciones
def detect_color_in_title(title):
    nl = normalize(title)
    if any(x in nl for x in ["camuflaj","camo","camuflad"]): return "Camuflaje"
    if any(x in nl for x in ["aqua","celeste"]): return "Aqua"
    if "azul marino" in nl: return "Azul Marino"
    if "azul" in nl or "blue" in nl: return "Azul"
    if "negr" in nl or "black" in nl: return "Negro"
    if "roj" in nl or "red" in nl: return "Rojo"
    if "rosa" in nl or "pink" in nl: return "Rosa"
    if any(x in nl for x in ["morado","violeta","purple","violet","purpura","púrpura"]): return "Morado"
    if "amarillo" in nl or "yellow" in nl: return "Amarillo"
    if "verde" in nl or "green" in nl: return "Verde"
    if "blanc" in nl or "white" in nl: return "Blanco"
    return None

def validate(cpid, model_target):
    r = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=20)
    if r.status_code != 200: return None
    p = r.json()
    title = p.get("name","") or ""
    nl = normalize(title)
    attrs = {a.get("id"): a.get("value_name") for a in (p.get("attributes") or [])}
    issues = []
    warn = []

    brand = attrs.get("BRAND") or ""
    model_attr = attrs.get("MODEL") or ""
    color_attr = attrs.get("COLOR") or ""
    line = attrs.get("LINE") or ""
    ptype = attrs.get("PRODUCT_TYPE") or ""

    # BRAND debe ser JBL (título dice JBL)
    if "jbl" in nl and "jbl" not in normalize(brand):
        issues.append(f"BRAND='{brand}' no es JBL")

    # MODEL debe matchear Go 4 / Go 3
    target_norm = normalize(model_target).replace(" ","")
    if target_norm not in normalize(model_attr).replace(" ",""):
        # mensaje suave si MODEL es solo "Go" o vacío, fuerte si es otro modelo
        if model_attr and any(other in normalize(model_attr) for other in ["flip","clip","charge","pulse"]):
            issues.append(f"MODEL='{model_attr}' es OTRO modelo (riesgo)")
        elif model_attr:
            warn.append(f"MODEL='{model_attr}' no contiene '{model_target}'")

    # Reacond/usado
    if any(k in nl for k in ["reacondic","refurb","usad"]):
        issues.append("título sugiere REACONDICIONADO/USADO")

    # Accesorios
    if any(k in nl for k in ["soporte","funda","cover","case","pared","correa","cable","cargador"]):
        issues.append("ACCESORIO, no es bocina principal")

    # Color title vs COLOR attribute
    title_color = detect_color_in_title(title)
    if color_attr and title_color:
        # Aceptar familias de morado
        morado_fam = ("morado","violeta","purple","violet","purpura","púrpura")
        if title_color == "Morado":
            if not any(x in normalize(color_attr) for x in morado_fam):
                warn.append(f"COLOR='{color_attr}' vs título='{title_color}'")
        elif normalize(title_color) not in normalize(color_attr) and normalize(color_attr) not in normalize(title_color):
            warn.append(f"COLOR='{color_attr}' vs título='{title_color}'")

    # PRODUCT_TYPE debe ser bocina/altavoz/parlante
    if ptype and not any(k in normalize(ptype) for k in ["bocina","parlante","altavoz","speaker","portátil","portable","portatil"]):
        issues.append(f"PRODUCT_TYPE='{ptype}' (¿accesorio?)")

    return {
        "cpid": cpid, "title": title[:80], "brand": brand, "model_attr": model_attr,
        "color_attr": color_attr, "title_color": title_color, "line": line,
        "ptype": ptype, "model_target": model_target,
        "issues": issues, "warnings": warn,
        "ok": len(issues) == 0,
        "already_published": cpid in already,
    }

print(f"\n=== Validando {len(found)} catálogos ===")
results = []
for cpid, info in found.items():
    v = validate(cpid, info["model"])
    if v:
        v["search_name"] = info["name"]
        results.append(v)
    time.sleep(0.4)

# Reporte
clean_new = [r for r in results if r["ok"] and not r["already_published"]]
dirty = [r for r in results if not r["ok"]]
existing = [r for r in results if r["already_published"]]
print(f"\nTotal: {len(results)}")
print(f"  Ya publicados: {len(existing)}")
print(f"  ❌ Con conflictos: {len(dirty)}")
print(f"  ✅ Limpios para publicar: {len(clean_new)}")

print("\n=== ❌ DESCARTAR ===")
for r in dirty[:30]:
    print(f"  {r['cpid']} ({r['model_target']}, color={r['title_color']}): {r['title']}")
    for i in r['issues']:
        print(f"    🚫 {i}")

print("\n=== ✅ PUBLICAR ===")
for r in clean_new:
    flag = " ⚠️" if r['warnings'] else ""
    print(f"  {r['cpid']} ({r['model_target']}, color={r['title_color']}){flag}: {r['title']}")

# Save
with open("go4_go3_audit.json", "w") as f:
    json.dump({
        "to_publish": clean_new,
        "to_discard": dirty,
        "already_published": existing,
    }, f, indent=2, ensure_ascii=False)

# TG
if TG and TGCID:
    msg = f"🛡️ *Auditoría Go 4 / Go 3 Negro*\n\n"
    msg += f"Total detectados: {len(results)}\n"
    msg += f"Ya publicados:    {len(existing)}\n"
    msg += f"❌ Descartar:     {len(dirty)}\n"
    msg += f"✅ Publicar:      *{len(clean_new)}*\n\n"
    by_color = {}
    for r in clean_new:
        mt = r['model_target']
        tc = r['title_color']
        k = f"{mt} {tc}"
        by_color[k] = by_color.get(k, 0) + 1
    msg += "*Distribución limpios:*\n"
    for k, n in sorted(by_color.items()):
        msg += f"• {k}: {n}\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )
