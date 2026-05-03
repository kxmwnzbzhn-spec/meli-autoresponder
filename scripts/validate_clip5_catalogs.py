#!/usr/bin/env python3
"""Audita 24 catálogos candidatos Clip 5 antes de publicar.
Detecta inconsistencias entre título y atributos (BRAND, MODEL, LINE, COLOR,
PRODUCT_TYPE, ITEM_CONDITION) para evitar infracciones MELI.

Genera 2 listas:
- LIMPIOS: título coherente con atributos → seguro publicar
- CONFLICTOS: atributos contradicen título → DESCARTAR (o intervención manual)
"""
import os, requests, json, time, re

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

CANDIDATES = {
    "Negro": ["MLM35713227", "MLM42622714", "MLM43541894", "MLM44713950",
              "MLM44963647", "MLM54533831", "MLM55738772", "MLM57996147",
              "MLM58837986", "MLM61814218"],
    "Azul":  ["MLM40329314", "MLM58592190", "MLM61825899"],
    "Rojo":  ["MLM44784289"],
    "Morado":["MLM44573520", "MLM44712007", "MLM45586155", "MLM47145951", "MLM49054893"],
    "Camuflaje":["MLM44712057", "MLM58616124"],
    "Rosa":  ["MLM44714337", "MLM63875183", "MLM64288232"],
    "Generico":["MLM44465821"],
}

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID, "client_secret": APP_SECRET, "refresh_token": RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}"}

def normalize(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

def check_catalog(cpid, expected_color):
    r = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=20)
    if r.status_code != 200:
        return {"cpid": cpid, "error": f"http {r.status_code}", "skip": True}
    p = r.json()
    title = p.get("name", "") or ""
    title_l = normalize(title)
    attrs = {a.get("id"): a.get("value_name") for a in (p.get("attributes") or [])}

    issues = []
    warnings = []

    # 1) BRAND check — título dice JBL → atributo BRAND debe ser JBL
    brand = attrs.get("BRAND") or ""
    if "jbl" in title_l:
        if "jbl" not in normalize(brand):
            issues.append(f"título dice 'JBL' pero BRAND='{brand}'")

    # 2) MODEL check — título dice Clip 5 → MODEL debería contener Clip 5
    model = attrs.get("MODEL") or ""
    if "clip 5" in title_l or "clip5" in title_l:
        if "clip 5" not in normalize(model) and "clip5" not in normalize(model):
            warnings.append(f"título dice 'Clip 5' pero MODEL='{model}'")

    # 3) LINE check
    line = attrs.get("LINE") or ""
    if "jbl" in title_l and line and "jbl" not in normalize(line) and "clip" not in normalize(line):
        warnings.append(f"LINE='{line}' inconsistente con título")

    # 4) PRODUCT_TYPE — debe ser bocina/parlante/altavoz
    ptype = attrs.get("PRODUCT_TYPE") or ""
    if ptype and not any(k in normalize(ptype) for k in ["bocina","parlante","altavoz","speaker","portátil","portable"]):
        issues.append(f"PRODUCT_TYPE='{ptype}' no es bocina (¿accesorio?)")

    # 5) Reacondicionado en título sin item_condition matching
    if any(k in title_l for k in ["reacondic", "refurb", "usad"]):
        issues.append(f"título sugiere REACONDICIONADO/USADO")

    # 6) Color en título coincide con expected_color
    color_attr = attrs.get("COLOR") or ""
    color_l = normalize(color_attr)
    expect_l = normalize(expected_color)
    if expect_l in ("morado","violeta","purpura","púrpura"):
        accept = ["morado","violeta","purpura","púrpura","purple","violet"]
    elif expect_l == "camuflaje":
        accept = ["camuflaje","camo","camuflada","camuflado"]
    elif expect_l == "generico":
        accept = []  # cualquier color OK
    else:
        accept = [expect_l]

    if expect_l != "generico" and color_l and not any(a in color_l for a in accept):
        # Solo warning si el COLOR no matchea — puede ser que MELI lo permite
        warnings.append(f"COLOR='{color_attr}' esperado '{expected_color}'")

    # 7) Wifi / sin bluetooth → flag
    if "wifi" in title_l and "bluetooth" not in title_l:
        issues.append("título solo menciona wifi (no es nuestro pool)")

    # 8) PACKAGE_INCLUDES o cosas raras como "soporte" o "cover"
    if any(k in title_l for k in ["soporte","funda","cover","case","pared"]):
        issues.append(f"título sugiere ACCESORIO no bocina")

    return {
        "cpid": cpid,
        "title": title[:80],
        "brand": brand,
        "model": model,
        "color_attr": color_attr,
        "ptype": ptype,
        "expected_color": expected_color,
        "issues": issues,
        "warnings": warnings,
        "ok": len(issues) == 0,
    }

# Process all
results = []
for color, cpids in CANDIDATES.items():
    for cpid in cpids:
        r = check_catalog(cpid, color)
        results.append(r)
        time.sleep(0.5)

clean = [r for r in results if r.get("ok")]
dirty = [r for r in results if not r.get("ok")]

print("=" * 70)
print(f"TOTAL: {len(results)} catálogos auditados")
print(f"✅ LIMPIOS: {len(clean)}")
print(f"❌ CON ISSUES: {len(dirty)}")
print("=" * 70)

print("\n=== ❌ CON CONFLICTOS (DESCARTAR) ===")
for r in dirty:
    print(f"\n  {r['cpid']} ({r['expected_color']})")
    print(f"    title: {r['title']}")
    print(f"    brand={r['brand']!r}  model={r['model']!r}  color_attr={r['color_attr']!r}")
    for i in r["issues"]:
        print(f"    🚫 {i}")

print("\n=== ⚠️  WARNINGS (publicar con precaución) ===")
warn_items = [r for r in clean if r.get("warnings")]
for r in warn_items:
    print(f"  {r['cpid']} ({r['expected_color']}): {r['warnings']}")

print("\n=== ✅ LIMPIOS (publicar) ===")
clean_no_warn = [r for r in clean if not r.get("warnings")]
for r in clean_no_warn:
    print(f"  {r['cpid']} ({r['expected_color']}): {r['title']}")

# Save report
with open("clip5_validation.json", "w") as f:
    json.dump({"clean": clean, "dirty": dirty}, f, indent=2, ensure_ascii=False)

# Telegram
if TG and TGCID:
    msg = f"🛡️ *Auditoría 24 Clip 5 catalogos*\n\n"
    msg += f"✅ Limpios: *{len(clean)}*\n"
    msg += f"❌ Conflictos: *{len(dirty)}*\n\n"
    if dirty:
        msg += "*Descartar (riesgo infracción):*\n"
        for r in dirty[:10]:
            iss = "; ".join(r['issues'][:2])
            msg += f"• `{r['cpid']}` ({r['expected_color']}): {iss[:80]}\n"
    if warn_items:
        msg += f"\n⚠️ Con warnings ({len(warn_items)}):\n"
        for r in warn_items[:8]:
            ww = "; ".join(r['warnings'][:1])
            msg += f"• `{r['cpid']}` ({r['expected_color']}): {ww[:80]}\n"
    msg += f"\n🎯 Para publicar: {len(clean_no_warn)} sin issues + {len(warn_items)} con warnings menores"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )
