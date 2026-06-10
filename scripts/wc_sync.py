"""Sincroniza órdenes WooCommerce con tracking de etiquetas.
Cada vez que una orden está en status=processing, se cuenta como etiqueta consumida.
Anti-duplicado: usamos sid='wc-{order_id}' como clave única.
"""
import os, sys, requests, time, json
from datetime import datetime, timezone, timedelta

WC_URL = os.environ.get("WC_BASE_URL","https://thealchemialab.com/wp-json/wc/v3").rstrip("/")
WC_KEY = os.environ["WC_CONSUMER_KEY"]
WC_SECRET = os.environ["WC_CONSUMER_SECRET"]
SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_SERVICE_KEY"]
TZ = timezone(timedelta(hours=-6))

def fetch_wc_orders():
    """Pull all processing + completed orders (last 30 days)."""
    orders = []
    after = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    for status in ("processing","completed"):
        page = 1
        while True:
            r = requests.get(f"{WC_URL}/orders",
                params={"status": status, "per_page": 100, "page": page, "after": after,
                        "consumer_key": WC_KEY, "consumer_secret": WC_SECRET},
                timeout=30)
            if r.status_code != 200:
                print(f"  WC API {status}: HTTP {r.status_code} {r.text[:200]}")
                break
            batch = r.json()
            if not batch: break
            orders.extend(batch)
            if len(batch) < 100: break
            page += 1
            time.sleep(0.2)
    return orders

def get_existing_wc_sids():
    sids = set(); offset = 0
    while True:
        r = requests.get(f"{SB_URL}/rest/v1/etiquetas_entregadas",
            params={"select":"sid","sid":"like.wc-*","limit":1000,"offset":offset},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=15)
        if r.status_code != 200: break
        rows = r.json()
        if not rows: break
        for row in rows: sids.add(row["sid"])
        if len(rows) < 1000: break
        offset += 1000
    return sids

def insert_records(recs):
    if not recs: return
    for i in range(0, len(recs), 500):
        chunk = recs[i:i+500]
        r = requests.post(f"{SB_URL}/rest/v1/etiquetas_entregadas",
            json=chunk,
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}",
                     "Content-Type":"application/json",
                     "Prefer":"resolution=merge-duplicates,return=minimal"}, timeout=30)
        if r.status_code not in (200,201,204):
            print(f"  INSERT HTTP {r.status_code}: {r.text[:200]}")

def cdmx_date_from_iso(iso_str):
    if not iso_str: return datetime.now(TZ).strftime("%Y-%m-%d")
    try:
        # WC date_created is in store timezone (UTC per the config given)
        dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ).strftime("%Y-%m-%d")
    except: return datetime.now(TZ).strftime("%Y-%m-%d")

def main():
    print(f"[wc_sync] {datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')} CDMX")
    orders = fetch_wc_orders()
    print(f"  Órdenes WC processing+completed (30d): {len(orders)}")
    existing = get_existing_wc_sids()
    print(f"  Ya en tracking: {len(existing)}")
    new = []
    for o in orders:
        sid = f"wc-{o['id']}"
        if sid in existing: continue
        items = o.get("line_items", [])
        title = items[0].get("name","Pedido WooCommerce") if items else "Pedido WooCommerce"
        new.append({
            "sid": sid,
            "account": "WooCommerce",
            "product_title": title[:200],
            "batch_date": cdmx_date_from_iso(o.get("date_created")),
        })
    print(f"  Nuevos: {len(new)}")
    if new:
        insert_records(new)
        print(f"  ✅ Insertados (acumulan al stock consumido)")
    print(f"\n  Resumen: {len(orders)} WC totales, {len(existing)+len(new)} en tracking")

if __name__ == "__main__":
    main()
