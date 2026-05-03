#!/usr/bin/env python3
"""Limpia duplicados Clip 5 en Raymundo:
- Cierra (status=closed) los 3 v2 duplicados
- Actualiza stock_config_raymundo: agrega catalog_product_id a v1 entries
- Quita entradas v2 duplicadas del config
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

# v2 items que son duplicados de v1
TO_CLOSE = [
    ("MLM2904676565", "Camuflaje v2 dup", "MLM44714150"),  # ya existe MLM2904674811 v1
    ("MLM2904700927", "Morado v2 dup",    "MLM44714111"),  # ya existe MLM5281123238 v1
    ("MLM5281124990", "Rojo v2 dup",      "MLM37361046"),  # ya existe MLM2904687737 v1
]

# Mapeo de v1 items a su catalog_product_id (para parchar el config)
V1_CATALOGS = {
    "MLM5281123238": "MLM44714111",  # Morado
    "MLM2904687737": "MLM37361046",  # Rojo
    "MLM5281123246": "MLM37110181",  # Negro
    "MLM2904687747": "MLM37110751",  # Azul
    "MLM2904674811": "MLM44714150",  # Camuflaje
}

# Auth
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "refresh_token": RT,
})
at = r.json()["access_token"]
H = {"Authorization": f"Bearer {at}", "Content-Type": "application/json"}

# 1) Cerrar los 3 duplicados
print("=== Cerrando duplicados v2 ===")
closed = []
for iid, label, cpid in TO_CLOSE:
    pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                      headers=H, json={"status": "closed"})
    print(f"  {iid} ({label}) → {pr.status_code}")
    if pr.status_code == 200:
        closed.append({"iid": iid, "label": label, "cpid": cpid})
    else:
        try: print(f"    err: {pr.json()}")
        except: print(f"    raw: {pr.text[:200]}")
    time.sleep(1)

# 2) Patchar stock_config_raymundo: agregar catalog_product_id a v1, quitar v2 dups
print("\n=== Actualizando stock_config_raymundo.json ===")
config_file = "stock_config_raymundo.json"
with open(config_file) as f:
    cfg = json.load(f)

# Remover entradas v2 duplicadas
for iid, _, _ in TO_CLOSE:
    if iid in cfg:
        del cfg[iid]
        print(f"  - removido del config: {iid}")

# Agregar catalog_product_id a v1
for iid, cpid in V1_CATALOGS.items():
    if iid in cfg:
        cfg[iid]["catalog_product_id"] = cpid
        print(f"  + cpid agregado a {iid}: {cpid}")

# Verificar v2 sobrevivientes (Negro 7W, Rojo cover) y agregar cpid
V2_KEEP = {
    "MLM2904700925": "MLM46022592",  # Rojo cover
    "MLM2904676579": "MLM46042650",  # Negro 7W
}
for iid, cpid in V2_KEEP.items():
    if iid in cfg:
        cfg[iid]["catalog_product_id"] = cpid
        print(f"  + cpid agregado a v2 keep {iid}: {cpid}")

with open(config_file, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# 3) Resumen
print("\n=== RESUMEN FINAL ===")
print(f"Cerrados: {len(closed)} duplicados")
clip5_in_cfg = [(k, v.get('label'), v.get('catalog_product_id'))
                for k, v in cfg.items() if 'Clip 5' in str(v.get('label',''))]
print(f"\nClip 5 activos en config:")
for iid, lbl, cpid in clip5_in_cfg:
    print(f"  {iid}: {lbl} (cat {cpid})")

# Telegram
if TG and TGCID:
    msg = f"🧹 *Cleanup duplicados Clip 5*\n\n"
    msg += f"Cerrados {len(closed)} duplicados v2:\n"
    for c in closed:
        msg += f"• `{c['iid']}` ({c['label']})\n"
    msg += f"\n📋 Clip 5 únicos activos en Raymundo: {len(clip5_in_cfg)}\n"
    for iid, lbl, _ in clip5_in_cfg:
        msg += f"• {lbl}: `{iid}`\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg},
        timeout=20,
    )
