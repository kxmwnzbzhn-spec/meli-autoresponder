"""Diagnóstico completo: revisa CADA publicación de catálogo de Raymundo,
consulta price_to_win, identifica perdedoras y por qué."""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me.get('id')
print(f"Cuenta: {me.get('nickname')} ({uid})\n")

# Cargar config
with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)
print(f"Config: {len(cfg)} items\n")

# Para cada item, query price_to_win + status
losing = []
winning = []
errors = []
for iid, meta in cfg.items():
    if not meta.get("catalog_war"):
        continue
    try:
        # Get item state
        it = requests.get(f"https://api.mercadolibre.com/items/{iid}",
                          headers=H, timeout=10,
                          params={"attributes":"id,title,price,status,catalog_listing,catalog_product_id,available_quantity"}).json()
        if it.get("status") != "active":
            continue
        cur_price = it.get("price")
        title = (it.get("title") or "")[:50]

        # price_to_win
        ptw = requests.get(
            f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2",
            headers=H, timeout=10
        ).json()
        ptw_price = ptw.get("price_to_win")
        ptw_status = ptw.get("status")

        floor = meta.get("floor_price", 199)
        ceiling = meta.get("ceiling_price", 1499)

        is_winning = ptw_status in ("winning",)

        info = {
            "iid": iid, "title": title, "label": meta.get("label","?"),
            "cur": cur_price, "ptw": ptw_price, "status": ptw_status,
            "floor": floor, "ceiling": ceiling,
        }
        if is_winning:
            winning.append(info)
        else:
            losing.append(info)
        time.sleep(0.2)
    except Exception as e:
        errors.append({"iid": iid, "err": str(e)[:100]})
        time.sleep(0.2)

print(f"\n=== RESUMEN ===")
print(f"Ganando 🏆:  {len(winning)}")
print(f"Perdiendo 💔: {len(losing)}")
print(f"Errores:     {len(errors)}")

print(f"\n=== PERDIENDO (first 25) ===")
for l in losing[:25]:
    needed_below = l["ptw"] - 1 if l["ptw"] else 0
    can_match = needed_below >= l["floor"] if needed_below else False
    flag = "📉 FLOOR_BLOCK" if not can_match else f"⚠️ podría bajar a {needed_below}"
    print(f"  {l['iid']} {l['label'][:30]} cur=${l['cur']} ptw=${l['ptw']} status={l['status']} floor=${l['floor']} → {flag}")

# TG
if TG and TGCID:
    msg = f"🩺 *Diagnóstico catalog war Raymundo*\n\n"
    msg += f"🏆 Ganando: {len(winning)}\n"
    msg += f"💔 Perdiendo: {len(losing)}\n\n"
    floor_blocked = [l for l in losing if l['ptw'] and l['ptw'] - 1 < l['floor']]
    can_fix = [l for l in losing if l['ptw'] and l['ptw'] - 1 >= l['floor']]
    msg += f"📉 Bloqueados por floor: *{len(floor_blocked)}* (necesitan bajar floor)\n"
    msg += f"⚠️ Bot debería arreglar: *{len(can_fix)}* (probar disparar war)\n\n"
    if floor_blocked[:5]:
        msg += "_Floor block (top 5):_\n"
        for l in floor_blocked[:5]:
            msg += f"• `{l['iid']}` {l['label'][:25]}: ptw=${l['ptw']} floor=${l['floor']}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": msg[:4000]}, timeout=20)

# Save report
with open("raymundo_war_diag.json","w") as f:
    json.dump({"winning": len(winning), "losing": losing, "errors": errors}, f, indent=2)
print(f"\nreporte guardado en raymundo_war_diag.json")
