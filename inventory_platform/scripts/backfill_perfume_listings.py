"""Backfill de listings no mapeados (perfumes y otros) por EAN/GTIN.

El backfill_listings.py original solo mapeó bocinas. Los perfumes están en
products (con barcode) pero sin listings vinculados. Este script:
  1. Por cada cuenta activa, lista items activos de MELI
  2. Para cada MLM que NO está ya en listings, fetch detalle
  3. Extrae GTIN/EAN de attributes
  4. Matchea contra products.barcode
  5. Si match → INSERT listing (mlm_id, account_id, sku, ...)
  6. Reporta matched/unmatched

Idempotente: skip MLMs ya en listings. Re-run seguro.

Uso:
    SUPABASE_DB_URL=... MELI_APP_ID=... MELI_APP_SECRET=... \\
        MELI_REFRESH_TOKEN_*=... TELEGRAM_* python backfill_perfume_listings.py
"""
import os, sys, requests, psycopg2

DSN = os.environ["SUPABASE_DB_URL"]
CID = os.environ["MELI_APP_ID"]
CS = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")


def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        print(f"[no tg] {msg}"); return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass


def refresh(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token",
                      data={"grant_type": "refresh_token", "client_id": CID,
                            "client_secret": CS, "refresh_token": rt}, timeout=20)
    return r.json().get("access_token") if r.status_code == 200 else None


def get_gtin(item):
    """Extrae GTIN/EAN de los attributes del item."""
    for attr in (item.get("attributes") or []):
        if attr.get("id") in ("GTIN", "EAN", "UPC"):
            v = attr.get("value_name") or attr.get("value_id")
            if v:
                return str(v).strip()
    return None


def list_active_items(user_id, token):
    """Pagina items activos del seller (offset hasta 1000, luego scan)."""
    H = {"Authorization": f"Bearer {token}"}
    ids = []
    offset = 0
    while offset < 1000:
        r = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search",
                         headers=H, params={"status": "active", "limit": 100, "offset": offset}, timeout=30)
        if r.status_code != 200:
            break
        body = r.json()
        results = body.get("results", [])
        ids.extend(results)
        total = body.get("paging", {}).get("total", 0)
        if offset + 100 >= total or not results:
            break
        offset += 100
    # Si hay >1000, usar scan
    if len(ids) >= 1000:
        scroll = None
        while True:
            params = {"status": "active", "search_type": "scan", "limit": 100}
            if scroll:
                params["scroll_id"] = scroll
            r = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search",
                             headers=H, params=params, timeout=30)
            if r.status_code != 200:
                break
            body = r.json()
            results = body.get("results", [])
            if not results:
                break
            ids.extend(results)
            scroll = body.get("scroll_id")
            if not scroll:
                break
    return list(set(ids))


def main():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()

    # Productos con barcode → map EAN→sku
    cur.execute("SELECT barcode, sku FROM products WHERE barcode IS NOT NULL AND archived=false")
    ean_to_sku = {str(b).strip(): s for b, s in cur.fetchall()}
    print(f"Productos con barcode: {len(ean_to_sku)}")

    # MLMs ya en listings (skip)
    cur.execute("SELECT mlm_id FROM listings")
    existing = {r[0] for r in cur.fetchall()}
    print(f"Listings existentes: {len(existing)}")

    cur.execute("SELECT id, nickname, meli_user_id, refresh_token_secret FROM accounts WHERE active=true ORDER BY nickname")
    accounts = cur.fetchall()

    total_matched = 0
    total_checked = 0
    total_unmatched = 0
    per_account = {}

    for aid, nick, user_id, secret_name in accounts:
        rt = os.environ.get(secret_name, "").strip()
        if not rt:
            continue
        token = refresh(rt)
        if not token:
            print(f"  {nick}: refresh failed")
            continue
        H = {"Authorization": f"Bearer {token}"}

        items = list_active_items(user_id, token)
        new_items = [m for m in items if m not in existing]
        print(f"\n{nick}: {len(items)} activos, {len(new_items)} sin mapear")

        matched = 0
        for mlm in new_items:
            total_checked += 1
            try:
                r = requests.get(f"https://api.mercadolibre.com/items/{mlm}", headers=H, timeout=20)
                if r.status_code != 200:
                    continue
                item = r.json()
            except Exception:
                continue
            gtin = get_gtin(item)
            sku = ean_to_sku.get(gtin) if gtin else None
            if not sku:
                total_unmatched += 1
                continue
            # INSERT listing
            cur.execute("""INSERT INTO listings (mlm_id, account_id, sku, title, price, status, available_quantity, last_sync)
                           VALUES (%s,%s,%s,%s,%s,%s,%s, now())
                           ON CONFLICT (mlm_id) DO UPDATE SET sku=EXCLUDED.sku, last_sync=now()""",
                        (mlm, aid, sku, item.get("title"), item.get("price"),
                         item.get("status"), item.get("available_quantity")))
            existing.add(mlm)
            matched += 1
            total_matched += 1
        per_account[nick] = matched
        print(f"  → {matched} perfumes mapeados por EAN")

    # Reporte
    lines = ["🔗 *Backfill perfume listings*", ""]
    lines.append(f"✓ Mapeados por EAN: *{total_matched}*")
    lines.append(f"  Revisados: {total_checked}")
    lines.append(f"  Sin match: {total_unmatched}")
    lines.append("")
    for nick, n in sorted(per_account.items(), key=lambda x: -x[1]):
        if n:
            lines.append(f"  • {nick}: {n}")
    msg = "\n".join(lines)
    print("\n" + msg)
    tg(msg)

    cur.close(); conn.close()


if __name__ == "__main__":
    main()
