"""Audita TODA la config Raymundo:
- Asegura floor por modelo: Go 4=$599, Go 3=$349, Clip 5=$799
- Si algún precio actual < floor → sube a floor
- Si label/model/color faltan → los detecta del título
"""
import os, requests, json, re

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

FLOORS = {
    "Go 4":   599,
    "Go 3":   349,
    "Clip 5": 799,
}
CEILING = 1499

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}

with open("stock_config_raymundo.json") as f:
    cfg = json.load(f)

def detect(title):
    t = title.lower().replace("bluetooth"," ")
    if "clip 5" in t or "clip5" in t: model = "Clip 5"
    elif "go 4" in t or "go4" in t:   model = "Go 4"
    elif "go 3" in t or "go3" in t:   model = "Go 3"
    else: return None, None
    if any(x in t for x in ["camuflaj","camo","camuflad"]): color = "Camuflaje"
    elif "azul marino" in t or "azul acero" in t: color = "Azul Marino"
    elif any(x in t for x in ["aqua","celeste"]): color = "Aqua"
    elif "negr" in t or "black" in t: color = "Negro"
    elif "roj" in t or " red" in t: color = "Rojo"
    elif "rosa" in t or "pink" in t: color = "Rosa"
    elif any(x in t for x in ["morado","violeta","purple","violet","purpura","púrpura"]): color = "Morado"
    elif " azul" in (" "+t) or " blue" in (" "+t): color = "Azul"
    else: color = "?"
    return model, color

# Listar todos los iids con catalog_listing
needs_floor_fix = 0
needs_meta_fix = 0
needs_price_fix = 0
fixed_meta = 0
fixed_price = 0

# Get item state in chunks
iids = list(cfg.keys())
for chunk_start in range(0, len(iids), 20):
    chunk = iids[chunk_start:chunk_start+20]
    r = requests.get("https://api.mercadolibre.com/items",
                     headers=H, params={"ids":",".join(chunk),
                       "attributes":"id,title,price,status,catalog_listing"},
                     timeout=20).json()
    for resp in r:
        if resp.get("code") != 200: continue
        it = resp.get("body")
        iid = it.get("id")
        if not it.get("catalog_listing"): continue
        if it.get("status") != "active": continue

        meta = cfg.get(iid, {})
        title = it.get("title","")
        cur_price = it.get("price")

        # Detectar model/color del título
        model_det, color_det = detect(title)
        meta_changed = False
        if not meta.get("model") and model_det:
            meta["model"] = model_det; meta_changed = True
        if not meta.get("color") and color_det:
            meta["color"] = color_det; meta_changed = True
        if not meta.get("label") and model_det and color_det:
            meta["label"] = f"{model_det} {color_det}"; meta_changed = True

        # Set floor
        model = meta.get("model") or model_det
        if model in FLOORS:
            target_floor = FLOORS[model]
            if meta.get("floor_price") != target_floor:
                meta["floor_price"] = target_floor
                meta_changed = True
                needs_floor_fix += 1
            meta.setdefault("ceiling_price", CEILING)
            meta.setdefault("catalog_war", True)
            meta.setdefault("auto_replenish", True)
            meta.setdefault("min_visible", 1)
            meta.setdefault("replenish_quantity", 1)

        # Si precio < floor, subir a floor
        if cur_price and meta.get("floor_price") and cur_price < meta["floor_price"]:
            new_p = meta["floor_price"]
            print(f"  💲 SUBIR {iid}: ${cur_price} → ${new_p}")
            pr = requests.put(f"https://api.mercadolibre.com/items/{iid}",
                              headers=H, json={"price": new_p})
            if pr.status_code == 200:
                fixed_price += 1
            needs_price_fix += 1

        if meta_changed:
            cfg[iid] = meta
            fixed_meta += 1

with open("stock_config_raymundo.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"\n=== RESUMEN ===")
print(f"Floors fijados:    {needs_floor_fix}")
print(f"Meta arreglada:    {fixed_meta}")
print(f"Precios subidos:   {fixed_price} / {needs_price_fix} necesarios")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id":TGCID,"parse_mode":"Markdown",
        "text":(
            f"🛠️ *Audit floor Raymundo*\n\n"
            f"Floors fijados: *{needs_floor_fix}*\n"
            f"Meta corregida: *{fixed_meta}*\n"
            f"Precios subidos: *{fixed_price}*\n\n"
            f"Floors aplicados:\n"
            f"• Go 4: \\$599\n"
            f"• Go 3: \\$349\n"
            f"• Clip 5: \\$799"
        )}, timeout=20)
