"""Re-mapea listings con SKU '%-XX' jalando data real de MELI (variation_attributes).

Regla CRÍTICA (MELI_RUNBOOK):
  - Color SIEMPRE de variation_attributes.id=COLOR.value_name
  - Fallback: GET /items/{id}/variations/{vid} → attribute_combinations
  - NUNCA derivar del título

Flujo por cada listing XX:
  1. Refresh access_token del account
  2. GET /items/{mlm_id}
  3. Si tiene variations[] (multi-color):
     a. Para cada variation: extraer color via attribute_combinations[id=COLOR].value_name
     b. Construir SKU canónico = {brand}-{model}-{color}
     c. INSERT product si no existe
     d. INSERT listing_variations (mlm_id, variation_id, sku, color, attrs)
     e. listings.sku queda como "PRIMARY_VARIATION" (primera variation o más común)
  4. Si NO tiene variations (single):
     a. Leer attributes[id=COLOR] del item directo
     b. Si "Caja Abierta"/"Reacondicionada"/"Espejo" en title → SKU con sufijo + condition
     c. UPDATE listings.sku al canónico
     d. INSERT product si no existe
"""
import os, sys, json, requests, psycopg2

DSN = os.environ["SUPABASE_DB_URL"]
CID = os.environ["MELI_APP_ID"]
CS = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

# Normalización de colores comunes (MELI los manda en varios formatos)
COLOR_NORMALIZE = {
    "negro": "NEGRO", "black": "NEGRO",
    "blanco": "BLANCO", "white": "BLANCO",
    "rojo": "ROJO", "red": "ROJO",
    "azul": "AZUL", "blue": "AZUL",
    "azul marino": "AZUL-MARINO", "marino": "AZUL-MARINO",
    "aqua": "AQUA", "celeste": "AQUA",
    "rosa": "ROSA", "pink": "ROSA",
    "morado": "MORADO", "purple": "MORADO", "purpura": "MORADO", "púrpura": "MORADO",
    "camuflado": "CAMUFLAJE", "camuflaje": "CAMUFLAJE",
    "verde": "VERDE", "green": "VERDE",
    "amarillo": "AMARILLO", "yellow": "AMARILLO",
    "gris": "GRIS", "gray": "GRIS", "grey": "GRIS",
    "naranja": "NARANJA", "orange": "NARANJA",
    "beige": "BEIGE",
    "menta": "MENTA",
}


def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        print(f"[no telegram] {msg}")
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass


def normalize_color(raw):
    if not raw:
        return None
    key = raw.strip().lower()
    return COLOR_NORMALIZE.get(key, raw.strip().upper().replace(" ", "-"))


def refresh_access(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token",
                      data={"grant_type": "refresh_token",
                            "client_id": CID, "client_secret": CS,
                            "refresh_token": rt}, timeout=20)
    if r.status_code != 200:
        return None
    return r.json().get("access_token")


def get_color_from_item(item):
    """Extrae color del nivel ITEM (single-variant)."""
    # Prefiere variation_attributes
    for attr in (item.get("variation_attributes") or []):
        if attr.get("id") == "COLOR":
            return normalize_color(attr.get("value_name"))
    # Fallback a attributes generales
    for attr in (item.get("attributes") or []):
        if attr.get("id") == "COLOR":
            return normalize_color(attr.get("value_name"))
    return None


def get_color_from_variation(variation):
    """Extrae color de una variation (multi-variant)."""
    for combo in (variation.get("attribute_combinations") or []):
        if combo.get("id") == "COLOR":
            return normalize_color(combo.get("value_name"))
    return None


def detect_special_condition(title):
    """Detecta marcadores especiales en title que NO son color sino condition/variante."""
    t = (title or "").lower()
    if "espejo" in t or "calidad 1:1" in t or "oem 1.1" in t:
        return ("ESPEJO", "generic_mirror")
    if "reacondicionad" in t or "refurbished" in t:
        return ("REACONDICIONADA", "refurbished")
    if "caja abierta" in t or "open box" in t:
        return ("CAJA-ABIERTA", "used")
    if "color sorpresa" in t or "sorpresa" in t:
        return ("SORPRESA", "new")
    return (None, None)


def ensure_product(cur, sku, modelo, color, brand, line, condition):
    """INSERT product si no existe (o si está archived, lo desarchiva)."""
    cur.execute("SELECT archived FROM products WHERE sku=%s", (sku,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """INSERT INTO products (sku, modelo, color, brand, line, condition, alert_threshold, notes)
               VALUES (%s,%s,%s,%s,%s,%s, 5, %s)""",
            (sku, modelo, color, brand, line, condition, f'Auto-creado por remap_xx_listings 2026-05-17')
        )
        return "created"
    elif row[0]:  # archived=true
        cur.execute("UPDATE products SET archived=false, archived_at=NULL WHERE sku=%s", (sku,))
        return "unarchived"
    return "exists"


def process_listing(cur, mlm_id, account_id, current_sku, access_token):
    """Procesa un listing XX. Devuelve dict con resultado."""
    H = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{mlm_id}", headers=H, timeout=20)
    except Exception as e:
        return {"mlm_id": mlm_id, "status": "fetch_error", "error": str(e)[:200]}
    if r.status_code != 200:
        return {"mlm_id": mlm_id, "status": f"http_{r.status_code}", "error": r.text[:200]}
    item = r.json()

    title = item.get("title", "")
    site = item.get("site_id", "MLM")
    # Inferir brand/line del current_sku (JBL-CLIP5-XX → brand=JBL, modelo=CLIP5)
    parts = current_sku.split("-")
    brand_inferred = parts[0] if parts else "GENERIC"
    modelo_inferred = parts[1] if len(parts) > 1 else "UNKNOWN"
    line_inferred = "Bocina"  # por ahora todos son bocinas

    special_color, special_condition = detect_special_condition(title)

    variations = item.get("variations") or []
    result = {"mlm_id": mlm_id, "title": title[:60], "variations_count": len(variations)}

    if variations:
        # Multi-variation: poblar listing_variations
        result["mode"] = "multi_variation"
        result["variants"] = []
        for v in variations:
            vid = v.get("id")
            color = get_color_from_variation(v)
            if not color and special_color:
                color = special_color
            if not color:
                color = "DESCONOCIDO"
            sku = f"{brand_inferred}-{modelo_inferred}-{color}"
            condition = special_condition or "new"
            action = ensure_product(cur, sku, modelo_inferred, color, brand_inferred, line_inferred, condition)
            cur.execute(
                """INSERT INTO listing_variations (mlm_id, variation_id, sku, color, attribute_combinations, price, available_quantity)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (mlm_id, variation_id) DO UPDATE SET sku=EXCLUDED.sku, color=EXCLUDED.color, last_sync=now()""",
                (mlm_id, vid, sku, color,
                 json.dumps(v.get("attribute_combinations") or []),
                 v.get("price"), v.get("available_quantity"))
            )
            result["variants"].append({"variation_id": vid, "color": color, "sku": sku, "action": action})
        # listings.sku queda en la primera variación (catch-all)
        first_sku = result["variants"][0]["sku"]
        cur.execute("UPDATE listings SET sku=%s WHERE mlm_id=%s", (first_sku, mlm_id))
        result["listings_sku_set_to"] = first_sku
    else:
        # Single-variation: leer color del item
        result["mode"] = "single"
        color = get_color_from_item(item)
        if not color:
            color = special_color or "DESCONOCIDO"
        sku = f"{brand_inferred}-{modelo_inferred}-{color}"
        condition = special_condition or "new"
        action = ensure_product(cur, sku, modelo_inferred, color, brand_inferred, line_inferred, condition)
        cur.execute("UPDATE listings SET sku=%s WHERE mlm_id=%s", (sku, mlm_id))
        result["new_sku"] = sku
        result["color"] = color
        result["product_action"] = action

    return result


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    # Cargar mapping account → (nick, refresh_token)
    cur.execute("SELECT id, nickname, refresh_token_secret FROM accounts WHERE active = true")
    accounts = {aid: (nick, os.environ.get(secret_name, "").strip())
                for aid, nick, secret_name in cur.fetchall()}

    # Tokens cache
    tokens = {}

    # Listings XX
    cur.execute("SELECT mlm_id, sku, account_id FROM listings WHERE sku LIKE %s ORDER BY sku", ("%-XX",))
    xx_listings = cur.fetchall()
    print(f"📋 Listings XX a procesar: {len(xx_listings)}")

    results = []
    for mlm_id, sku, account_id in xx_listings:
        nick, rt = accounts.get(account_id, (None, None))
        if not rt:
            results.append({"mlm_id": mlm_id, "sku": sku, "status": "no_token_for_account"})
            continue
        if account_id not in tokens:
            tokens[account_id] = refresh_access(rt)
            if not tokens[account_id]:
                results.append({"mlm_id": mlm_id, "sku": sku, "status": "refresh_failed"})
                continue
        access = tokens[account_id]
        print(f"\n--- {mlm_id} (was {sku}, account={nick}) ---")
        res = process_listing(cur, mlm_id, account_id, sku, access)
        results.append(res)
        print(f"   {res.get('mode', 'error')}: {res}")

    conn.commit()
    cur.close()
    conn.close()

    # Telegram summary
    multi = [r for r in results if r.get("mode") == "multi_variation"]
    single = [r for r in results if r.get("mode") == "single"]
    errors = [r for r in results if r.get("status") and not r.get("mode")]

    lines = [f"🔄 *Remap XX listings*", ""]
    lines.append(f"✓ Multi-variation: {len(multi)}")
    for r in multi:
        lines.append(f"  • `{r['mlm_id']}` → {len(r['variants'])} variants → primary `{r['listings_sku_set_to']}`")
    lines.append("")
    lines.append(f"✓ Single-variation: {len(single)}")
    for r in single:
        lines.append(f"  • `{r['mlm_id']}` → `{r['new_sku']}` (color={r['color']})")
    if errors:
        lines.append("")
        lines.append(f"❌ Errors: {len(errors)}")
        for r in errors:
            lines.append(f"  • `{r['mlm_id']}`: {r.get('status', 'unknown')}")

    msg = "\n".join(lines)
    print("\n" + msg)
    tg(msg)


if __name__ == "__main__":
    main()
