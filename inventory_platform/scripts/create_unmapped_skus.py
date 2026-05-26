"""create_unmapped_skus.py — Cataloga listings MELI sin SKU.

Por cada cuenta activa:
  1. Lista items activos.
  2. Para los que NO están en listings: propone SKU determinístico desde el título
     (PERF-ALCHEMIA-*, PERF-LV-*, PERF-BYREDO-*, ASVA-SECADORA, ASVA-BUDS-2, etc.)
  3. Si la propuesta apunta a un SKU EXISTENTE → solo inserta listing (mapeo).
  4. Si la propuesta es un SKU NUEVO → INSERT product (sin stock) + listing.
  5. Multi-variación: por cada variación, parsea color y mapea o crea por color.

Stock arranca en 0 para SKUs nuevos. Sales de SKUs sin stock se marcan 'error/oversell'
hasta que el usuario seedee con un conteo físico. Esto es señal limpia: catálogo completo,
inventario pendiente.

Idempotente. --dry-run muestra propuestas sin escribir.

Uso:
    SUPABASE_DB_URL=... TOKEN_READ_SECRET=... WORKER_BASE=... \\
        python create_unmapped_skus.py [--dry-run] [--account NICK] [--max-seconds 280]
"""
import os, sys, re, time, argparse, requests, psycopg2
from concurrent.futures import ThreadPoolExecutor

DSN = os.environ["SUPABASE_DB_URL"]
WORKER_BASE = os.environ.get("WORKER_BASE", "").rstrip("/")
TOKEN_READ_SECRET = os.environ.get("TOKEN_READ_SECRET", "")

DEVO_KEYS = ("caja abierta", "calidad espejo", "espejo ip", "reacondicionad", "refurbished", "oem 1.1")

# ------- Slug -------
TILDES = str.maketrans({"Á":"A","À":"A","Ä":"A","Â":"A","É":"E","È":"E","Ë":"E","Ê":"E",
                        "Í":"I","Ì":"I","Ï":"I","Î":"I","Ó":"O","Ò":"O","Ö":"O","Ô":"O",
                        "Ú":"U","Ù":"U","Ü":"U","Û":"U","Ñ":"N","Ç":"C"})
def slug(s, maxlen=60):
    if not s: return ""
    s = s.upper().translate(TILDES)
    s = re.sub(r"[^A-Z0-9]+", "-", s).strip("-")
    return s[:maxlen]

def strip_noise(s):
    """Quita ruido común de títulos de perfume (volumen, tipo, género)."""
    s = re.sub(r"\b(eau de parfum|eau de toilette|edp|edt|edc|parfum|spray|hidratante)\b", "", s, flags=re.I)
    s = re.sub(r"\b\d+\s*ml\b", "", s, flags=re.I)
    s = re.sub(r"\b\d+\s*oz\b", "", s, flags=re.I)
    s = re.sub(r"\b(unisex|hombre|mujer|femenino|masculino|para hombre|para mujer|caballero|dama)\b", "", s, flags=re.I)
    s = re.sub(r"^\s*perfume\s+", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ------- Modelo/color speakers (catálogo existente) -------
def parse_speaker_model(t):
    if "xb100" in t or ("sony" in t and "xb" in t): return ("SONY", "XB100")
    if "clip 5" in t or "clip5" in t: return ("JBL", "CLIP5")
    if "clip 4" in t or "clip4" in t: return ("JBL", "CLIP4")
    if "go 4" in t or "go4" in t: return ("JBL", "GO4")
    if "go 3" in t or "go3" in t: return ("JBL", "GO3")
    if "flip 7" in t or "flip7" in t: return ("JBL", "FLIP7")
    if "charge 6" in t or "charge6" in t: return ("JBL", "CHARGE6")
    if "grip" in t and "jbl" in t: return ("JBL", "GRIP")
    if "bose" in t and "soundlink" in t: return ("BOSE", "BOSE")
    if "bose" in t: return ("BOSE", "BOSE")
    return (None, None)

def parse_color(t):
    if "camufl" in t or "verde musgo" in t: return "CAMUFLAJE"
    if "azul marino" in t or " marino" in t: return "MARINO"
    if "celeste" in t: return "CELESTE"
    if "aqua" in t: return "AQUA"
    if "morad" in t or "purpura" in t or "púrpura" in t or "violeta" in t: return "MORADO"
    if "rosa" in t or "rosado" in t or "pink" in t: return "ROSA"
    if "roja" in t or "rojo" in t or " red" in t: return "ROJO"
    if "azul" in t or "blue" in t: return "AZUL"
    if "negr" in t or "black" in t: return "NEGRO"
    if "blanc" in t or "white" in t: return "BLANCO"
    if "naranja" in t or "orange" in t: return "NARANJA"
    return None

def speaker_sku(title, sku_set):
    t = title.lower()
    brand, model = parse_speaker_model(t)
    color = parse_color(t)
    if not model: return None
    if model == "BOSE":
        c = f"BOSE-{color}" if color in ("NEGRO","BLANCO") else None
        return c if c in sku_set else None
    if model == "XB100":
        c = f"SONY-XB100-{color or 'NEGRO'}"
        return c if c in sku_set else None
    if not color: return None
    cand = f"JBL-{model}-{color}"
    if cand in sku_set: return cand
    if model == "GO4" and color == "CELESTE":
        c = "JBL-GO4-AQUA"
        if c in sku_set: return c
    return None

# ------- Propuesta de SKU NUEVO desde título -------
BRANDS_PERF = ["byredo","gucci","marc jacobs","viktor & rolf","viktor rolf","initio",
               "tom ford","jo malone","creed","maison francis kurkdjian","dior","chanel",
               "carolina herrera","paco rabanne","yves saint laurent","valentino","versace",
               "armaf","mancera","montale","afnan","rasasi","lattafa","mayar","khamrah",
               "orientica","ajmal","swiss arabian","asad","fakhar","lord","calvin klein",
               "burberry","hugo boss"]

# Marcas donde el NOMBRE va antes de la marca: "Perfume [Nombre] The Alchemia Lab ..."
def _extract_name_before(t, brand_token):
    """Devuelve el nombre que viene antes de la marca, limpio de prefijos genéricos."""
    if brand_token not in t: return None
    before = t.split(brand_token, 1)[0]
    # quitar prefijos comunes
    before = re.sub(r"^\s*perfume\s+(?:femenino|hombre|unisex|para hombre|para mujer)\s+", "", before, flags=re.I)
    before = re.sub(r"^\s*perfume\s+", "", before, flags=re.I)
    before = strip_noise(before)
    before = re.sub(r"\s+", " ", before).strip(" .,-|")
    if not before or len(before) < 3: return None
    # tomar máximo 5 palabras significativas
    words = before.split()
    return " ".join(words[:5])

def propose_new_sku(title):
    t = title.lower().strip()
    # ASVA Electronics
    if "asva" in t and ("secadora" in t or "secador" in t):
        return ("ASVA-SECADORA-IONICA-DIGITAL", "Secadora Asva Iónica", "ASVA", "ELECTRONICS")
    if "asva" in t and ("buds 2" in t or "buds2" in t) and ("audifono" in t or "audífono" in t or "tws" in t or "earphone" in t):
        return ("ASVA-BUDS-2", "Asva Buds 2 TWS", "ASVA", "AUDIO")
    if "asva" in t and ("dashcam" in t or "dvr" in t or "dc170" in t):
        if "dvr-3" in t or "dvr3" in t: return ("ASVA-DASHCAM-DVR-3","Dashcam Asva DVR-3","ASVA","CAR")
        if "dc170" in t or "dc 170" in t: return ("ASVA-DASHCAM-DC170","Dashcam Asva DC170","ASVA","CAR")
        return ("ASVA-DASHCAM","Dashcam Asva","ASVA","CAR")
    # Xiaomi Redmi Buds
    if "xiaomi" in t and "redmi buds" in t:
        if "4 lite" in t: return ("XIAOMI-REDMI-BUDS-4-LITE","Xiaomi Redmi Buds 4 Lite","XIAOMI","AUDIO")
        if "5" in t: return ("XIAOMI-REDMI-BUDS-5","Xiaomi Redmi Buds 5","XIAOMI","AUDIO")
        return ("XIAOMI-REDMI-BUDS","Xiaomi Redmi Buds","XIAOMI","AUDIO")
    # JBL knockoff / unknown padrão
    if "jbl" in t and ("padrao" in t or "padrão" in t or "padr&atilde;o" in t):
        c = parse_color(t) or "GENERICO"
        return (f"JBL-PADRAO-{c}",f"JBL Padrão {c.title()}","JBL","SPEAKER-OTRO")
    # Bocina genérica bluetooth
    if ("bocina" in t or "altavoz" in t or "parlante" in t or "speaker" in t) and "bluetooth" in t and not "jbl" in t and not "bose" in t and not "sony" in t:
        c = parse_color(t) or "GENERICO"
        # Ip67/IP X rating + watts
        m = re.search(r"\b(\d{2,3})\s*w\b", t)
        watts = f"-{m.group(1)}W" if m else ""
        return (f"BOCINA-GENERICA{watts}-{c}", f"Bocina Genérica Bluetooth {c.title()}","GENERICA","SPEAKER")
    # House brand Alchemia: nombre va ANTES de la marca
    for brand_token in ("the alchemia lab","alchemia lab"):
        if brand_token in t:
            name = _extract_name_before(t, brand_token)
            if name: return (f"PERF-ALCHEMIA-{slug(name,50)}", f"The Alchemia Lab {name.title()}","ALCHEMIA","PERFUME")
    # LV Perfume Studio: nombre antes
    for brand_token in ("lv perfume studio","lv perfume"):
        if brand_token in t:
            name = _extract_name_before(t, brand_token)
            if name: return (f"PERF-LV-{slug(name,50)}", f"LV Perfume Studio {name.title()}","LV","PERFUME")
    # Marcas con nombre DESPUÉS (estándar)
    for brand in BRANDS_PERF:
        if brand in t:
            # Extraer nombre después de la marca
            rest = t.split(brand, 1)[1]
            rest = strip_noise(rest)
            # corta en separadores
            rest = re.split(r"[,|·•\-–—]| con | with ", rest, maxsplit=1)[0].strip()
            # quitar palabras tipo "para hombre", "set de"
            rest = re.sub(r"\b(set de \d+ pzs?\.?|set de \d+ pzas?\.?)\b", "SET", rest, flags=re.I)
            words = rest.split()
            # toma hasta 5 palabras significativas
            name = " ".join(words[:5]).strip()
            brand_norm = brand.replace("the alchemia lab","ALCHEMIA").replace("alchemia lab","ALCHEMIA").replace("alchemia","ALCHEMIA")
            brand_norm = brand_norm.replace("lv perfume studio","LV").replace("lv perfume","LV")
            brand_norm = brand_norm.replace("viktor & rolf","VIKTOR-ROLF").replace("viktor rolf","VIKTOR-ROLF")
            brand_norm = brand_norm.replace("marc jacobs","MARC-JACOBS")
            brand_norm = brand_norm.replace("maison francis kurkdjian","MFK")
            brand_norm = brand_norm.replace("tom ford","TOM-FORD")
            brand_norm = brand_norm.replace("jo malone","JO-MALONE")
            brand_norm = brand_norm.replace("paco rabanne","PACO-RABANNE")
            brand_norm = brand_norm.replace("yves saint laurent","YSL")
            brand_norm = brand_norm.replace("carolina herrera","CAROLINA-HERRERA")
            brand_norm = slug(brand_norm, 30)
            tail = slug(name, 50)
            if not tail: return None
            return (f"PERF-{brand_norm}-{tail}", f"{brand.title()} {name}", brand_norm.split('-')[0].title(), "PERFUME")
    return None

# ------- MELI helpers -------
def get_token(nick):
    try:
        r = requests.get(f"{WORKER_BASE}/token/{nick}", headers={"Authorization": f"Bearer {TOKEN_READ_SECRET}"}, timeout=25)
        return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None

def list_active(user_id, token):
    H = {"Authorization": f"Bearer {token}"}
    ids, offset = [], 0
    while offset < 1000:
        try:
            r = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search",
                             headers=H, params={"status": "active","limit":100,"offset":offset}, timeout=30)
        except Exception: break
        if r.status_code != 200: break
        b = r.json(); res = b.get("results", []); ids += res
        total = b.get("paging",{}).get("total",0)
        if offset + 100 >= total or not res: break
        offset += 100
    return list(dict.fromkeys(ids))

def multiget(ids, token):
    H = {"Authorization": f"Bearer {token}"}
    out = {}
    def chunk(c):
        try:
            r = requests.get("https://api.mercadolibre.com/items", headers=H,
                             params={"ids":",".join(c),"attributes":"id,title,variations,status,attributes"}, timeout=30)
            if r.status_code == 200: return r.json()
        except Exception: pass
        return []
    chunks = [ids[i:i+20] for i in range(0,len(ids),20)]
    with ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(chunk, chunks):
            for entry in (res or []):
                body = entry.get("body") if isinstance(entry, dict) else None
                if body and body.get("id"):
                    out[body["id"]] = body
    return out

# ------- Main -------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--account", default=None)
    ap.add_argument("--max-seconds", type=int, default=280)
    args = ap.parse_args()
    t0 = time.time()

    conn = psycopg2.connect(DSN); conn.autocommit = False; cur = conn.cursor()
    cur.execute("SELECT sku FROM products WHERE archived=false")
    sku_set = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT mlm_id FROM listings")
    existing_listings = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT id, nickname, meli_user_id FROM accounts WHERE active=true ORDER BY nickname")
    accounts = cur.fetchall()
    conn.commit()
    if args.account:
        accounts = [a for a in accounts if (a[1] or "").lower() == args.account.lower()]

    new_skus = {}     # sku -> (display, brand, line)
    new_listings = []  # (mlm, account_id, sku, title, status, warehouse)
    unparseable = []   # (mlm, title)
    multivar_skip = []

    for aid, nick, uid in accounts:
        if time.time() - t0 > args.max_seconds: print("⏱ max-seconds"); break
        tok = get_token((nick or "").upper())
        if not tok or not uid: print(f"  {nick}: sin token/uid"); continue
        ids = list_active(uid, tok)
        new_ids = [i for i in ids if i not in existing_listings]
        details = multiget(new_ids, tok) if new_ids else {}
        a_map = a_create = a_un = a_mv = 0
        for mlm, item in details.items():
            title = item.get("title") or ""
            variations = item.get("variations") or []
            t = title.lower()
            wh = "devolucion" if any(k in t for k in DEVO_KEYS) else "bodega_main"
            if len(variations) > 1:
                # multivar: NOT handled here, skip (handle via listing_variations dedicated script)
                a_mv += 1; multivar_skip.append((mlm, title)); continue
            # 1) Try existing speaker catalog
            sku = speaker_sku(title, sku_set)
            if sku:
                new_listings.append((mlm, aid, sku, title, item.get("status"), wh))
                existing_listings.add(mlm); a_map += 1; continue
            # 2) Propose new SKU
            prop = propose_new_sku(title)
            if not prop:
                a_un += 1; unparseable.append((mlm, title)); continue
            sku, display, brand, line = prop
            if sku not in sku_set:
                new_skus[sku] = (display, brand, line)
                sku_set.add(sku)
            new_listings.append((mlm, aid, sku, title, item.get("status"), wh))
            existing_listings.add(mlm); a_create += 1
        print(f"{nick}: activos={len(ids)} new={len(new_ids)} mapeados-catalogo={a_map} nuevos-SKU={a_create} multivar(skip)={a_mv} unparseable={a_un}")

    print(f"\n=== Resumen ===")
    print(f"SKUs nuevos a crear: {len(new_skus)}")
    print(f"Listings nuevos a insertar: {len(new_listings)}")
    print(f"Multi-variación (skip, mapeo manual): {len(multivar_skip)}")
    print(f"No-parseable: {len(unparseable)}")
    print(f"\n--- SKUs nuevos (primeros 40) ---")
    for sku, (disp, brand, line) in list(new_skus.items())[:40]:
        print(f"  {sku:55s} | {brand}/{line} | {disp[:50]}")
    if len(new_skus) > 40: print(f"  ... y {len(new_skus)-40} más")
    print(f"\n--- No-parseable (primeros 10) ---")
    for mlm,title in unparseable[:10]: print(f"  {mlm}: {title[:70]}")

    if args.dry_run:
        print("\n[DRY-RUN] Nada escrito.")
        cur.close(); conn.close(); return

    # APLICAR
    for sku, (disp, brand, line) in new_skus.items():
        cur.execute(
            """INSERT INTO products (sku, modelo, brand, line, condition, archived, notes)
               VALUES (%s,%s,%s,%s,'new', false, 'auto-creado desde título MELI')
               ON CONFLICT (sku) DO NOTHING""",
            (sku, disp[:120], brand, line)
        )
    for mlm, aid, sku, title, status, wh in new_listings:
        cur.execute(
            """INSERT INTO listings (mlm_id, account_id, sku, title, status, warehouse_default, last_sync)
               VALUES (%s,%s,%s,%s,%s,%s, now())
               ON CONFLICT (mlm_id) DO UPDATE SET sku=EXCLUDED.sku, warehouse_default=EXCLUDED.warehouse_default, last_sync=now()""",
            (mlm, aid, sku, title[:250], status, wh)
        )
    conn.commit()
    print(f"\n✓ Aplicado: {len(new_skus)} productos, {len(new_listings)} listings.")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
