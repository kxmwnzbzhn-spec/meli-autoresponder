"""backfill_listings_by_title.py — Mapea listings MELI a SKU por título (modelo+color).

El backfill por EAN/GTIN no cubre las bocinas (los títulos llevan el color, no GTIN).
Este script, por cada cuenta activa:
  1. Lista items activos del seller (search API).
  2. Multiget de títulos (/items?ids=...).
  3. Parsea modelo (Go3/Go4/Clip5/Flip7/Charge6/Sony XB100/Bose) + color del título.
  4. Resuelve el SKU canónico contra products (catálogo real).
  5. Detecta listings de devolución (espejo/caja abierta/reacondicionada) → warehouse 'devolucion'.
  6. INSERT en listings (ON CONFLICT (mlm_id) skip), solo listings de UNA variación/color.
     Listings multi-variación se reportan para mapeo manual (listing_variations).

Idempotente. --dry-run para previsualizar.

Uso:
    SUPABASE_DB_URL=... TOKEN_READ_SECRET=... WORKER_BASE=... \\
        python backfill_listings_by_title.py [--dry-run] [--account NICK] [--max-seconds 280]
"""
import os, sys, time, argparse, requests, psycopg2
from concurrent.futures import ThreadPoolExecutor

DSN = os.environ["SUPABASE_DB_URL"]
WORKER_BASE = os.environ.get("WORKER_BASE", "https://meli-webhook.elite-market-1779161651.workers.dev").rstrip("/")
TOKEN_READ_SECRET = os.environ.get("TOKEN_READ_SECRET", "")

DEVO_KEYS = ("caja abierta", "calidad espejo", "espejo ip", "reacondicionad", "refurbished", "oem 1.1")

def get_token(nick):
    try:
        r = requests.get(f"{WORKER_BASE}/token/{nick}", headers={"Authorization": f"Bearer {TOKEN_READ_SECRET}"}, timeout=25)
        return r.json().get("access_token") if r.status_code == 200 else None
    except Exception:
        return None


def parse_model(t):
    if "xb100" in t or ("sony" in t and "xb" in t): return ("SONY", "XB100")
    if "clip 5" in t or "clip5" in t: return ("JBL", "CLIP5")
    if "clip 4" in t or "clip4" in t: return ("JBL", "CLIP4")
    if "go 4" in t or "go4" in t: return ("JBL", "GO4")
    if "go 3" in t or "go3" in t: return ("JBL", "GO3")
    if "flip 7" in t or "flip7" in t: return ("JBL", "FLIP7")
    if "charge 6" in t or "charge6" in t: return ("JBL", "CHARGE6")
    if "grip" in t and "jbl" in t: return ("JBL", "GRIP")
    if "bose" in t: return ("BOSE", "BOSE")
    return (None, None)


def parse_color(t):
    if "camufl" in t or "verde musgo" in t or "musgo" in t: return "CAMUFLAJE"
    if "azul marino" in t or "marino" in t: return "MARINO"
    if "celeste" in t: return "CELESTE"
    if "aqua" in t: return "AQUA"
    if "morad" in t or "púrpura" in t or "purpura" in t or "violeta" in t: return "MORADO"
    if "rosa" in t or "rosado" in t or "pink" in t: return "ROSA"
    if "roja" in t or "rojo" in t or " red" in t: return "ROJO"
    if "azul" in t or "blue" in t: return "AZUL"
    if "negr" in t or "black" in t: return "NEGRO"
    if "blanc" in t or "white" in t: return "BLANCO"
    return None


def resolve_sku(title, sku_set):
    t = title.lower()
    brand, model = parse_model(t)
    color = parse_color(t)
    if not model:
        return None, "no_model"
    if model == "BOSE":
        cand = f"BOSE-{color}" if color in ("NEGRO", "BLANCO") else None
        return (cand if cand in sku_set else None), ("bose" if cand else "bose_no_color")
    if model == "XB100":
        cand = f"SONY-XB100-{color or 'NEGRO'}"
        return (cand if cand in sku_set else None), "sony"
    if not color:
        return None, "no_color"
    cand = f"JBL-{model}-{color}"
    if cand in sku_set:
        return cand, "ok"
    # fallbacks por modelo
    if model == "GO4" and color == "CELESTE":
        c = "JBL-GO4-AQUA"
        if c in sku_set: return c, "celeste->aqua"
    if model == "GO4" and color == "AQUA":
        c = "JBL-GO4-AQUA"
        if c in sku_set: return c, "ok"
    return None, f"no_sku:{model}-{color}"


def list_active_items(user_id, token):
    H = {"Authorization": f"Bearer {token}"}
    ids, offset = [], 0
    while offset < 1000:
        try:
            r = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search",
                             headers=H, params={"status": "active", "limit": 100, "offset": offset}, timeout=30)
        except Exception:
            break
        if r.status_code != 200: break
        b = r.json(); res = b.get("results", []); ids += res
        total = b.get("paging", {}).get("total", 0)
        if offset + 100 >= total or not res: break
        offset += 100
    return list(dict.fromkeys(ids))


def multiget(ids, token):
    """Devuelve dict mlm-> item(title, variations) usando /items?ids (20 por call)."""
    H = {"Authorization": f"Bearer {token}"}
    out = {}
    def chunk(c):
        try:
            r = requests.get("https://api.mercadolibre.com/items",
                             headers=H, params={"ids": ",".join(c), "attributes": "id,title,variations,status"}, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception:
            return []
        return []
    chunks = [ids[i:i+20] for i in range(0, len(ids), 20)]
    with ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(chunk, chunks):
            for entry in (res or []):
                body = entry.get("body") if isinstance(entry, dict) else None
                if body and body.get("id"):
                    out[body["id"]] = body
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--account", default=None, help="solo esta cuenta (nickname)")
    ap.add_argument("--max-seconds", type=int, default=280)
    args = ap.parse_args()
    t0 = time.time()

    conn = psycopg2.connect(DSN); conn.autocommit = False; cur = conn.cursor()
    cur.execute("SELECT sku FROM products WHERE archived=false")
    sku_set = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT mlm_id FROM listings")
    existing = set(r[0] for r in cur.fetchall())
    cur.execute("SELECT id, nickname, meli_user_id FROM accounts WHERE active=true ORDER BY nickname")
    accounts = cur.fetchall()
    conn.commit()

    if args.account:
        accounts = [a for a in accounts if (a[1] or "").lower() == args.account.lower()]

    tot_match = tot_insert = tot_unmatched = tot_multivar = 0
    unmatched_samples = []
    for aid, nick, uid in accounts:
        if time.time() - t0 > args.max_seconds:
            print("⏱ max-seconds"); break
        token = get_token((nick or "").upper())
        if not token or not uid:
            print(f"  {nick}: sin token/uid, skip"); continue
        ids = list_active_items(uid, token)
        new_ids = [i for i in ids if i not in existing]
        details = multiget(new_ids, token) if new_ids else {}
        a_match = a_ins = a_un = a_mv = 0
        for mlm, item in details.items():
            variations = item.get("variations") or []
            title = item.get("title") or ""
            if len(variations) > 1:
                a_mv += 1; tot_multivar += 1
                continue  # multi-variación → mapeo manual (listing_variations)
            sku, why = resolve_sku(title, sku_set)
            if not sku:
                a_un += 1; tot_unmatched += 1
                if len(unmatched_samples) < 20:
                    unmatched_samples.append(f"{mlm}: {title[:60]} ({why})")
                continue
            a_match += 1; tot_match += 1
            t = title.lower()
            wh = "devolucion" if any(k in t for k in DEVO_KEYS) else "bodega_main"
            if not args.dry_run:
                cur.execute(
                    """INSERT INTO listings (mlm_id, account_id, sku, title, status, warehouse_default, last_sync)
                       VALUES (%s,%s,%s,%s,%s,%s, now())
                       ON CONFLICT (mlm_id) DO UPDATE SET sku=EXCLUDED.sku, warehouse_default=EXCLUDED.warehouse_default, last_sync=now()""",
                    (mlm, aid, sku, title[:250], item.get("status"), wh)
                )
                existing.add(mlm); a_ins += 1; tot_insert += 1
            else:
                print(f"  [DRY] {nick} {mlm} -> {sku} @ {wh} | {title[:55]}")
        if not args.dry_run:
            conn.commit()
        print(f"{nick}: activos={len(ids)} nuevos={len(new_ids)} match={a_match} insert={a_ins} multivar={a_mv} unmatched={a_un}")

    print(f"\nTOTAL match={tot_match} insert={tot_insert} multivar(skip)={tot_multivar} unmatched={tot_unmatched}")
    if unmatched_samples:
        print("unmatched ej:")
        for s in unmatched_samples: print("   ", s)
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
