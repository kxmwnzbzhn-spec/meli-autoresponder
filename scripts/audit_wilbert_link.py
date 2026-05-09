"""Audit profundo de la cuenta WILBERT — por qué MELI la bloqueó por 'ventas vinculadas'.
Cruza datos de buyers/shipping/items entre WILBERT y las otras 8 cuentas para
encontrar el patrón real que MELI detectó como vinculado.
"""
import os, requests, time, json
from collections import defaultdict, Counter

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

# Todas las cuentas para cross-check
ALL_ACCS = {
    "JUAN":         os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":     os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASGARI":       os.environ.get("MELI_REFRESH_TOKEN_ASGARI"),
    "MILDRED":      os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "WILBERT":      os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "RAYMUNDO":     os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "ANGEL_DAMIAN": os.environ.get("MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
    "RAYMUNDO_MAY": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
    "DILCIE":       os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
}

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    return r.get("access_token")

# 1. Sacar UIDs de TODAS las cuentas
ACC_TO_UID = {}
ACC_TO_TOK = {}
for acc, rt in ALL_ACCS.items():
    if not rt: continue
    at = tok(rt)
    if not at: continue
    me = requests.get("https://api.mercadolibre.com/users/me",
                      headers={"Authorization":f"Bearer {at}"}, timeout=15).json()
    if me.get("id"):
        ACC_TO_UID[acc] = me["id"]
        ACC_TO_TOK[acc] = at
        print(f"  {acc}: uid={me['id']}")

print(f"\nTotal cuentas conectadas: {len(ACC_TO_UID)}")

# 2. Bajar TODAS las órdenes de WILBERT (paid + cancelled últimos 60 días)
W_AT = ACC_TO_TOK.get("WILBERT")
W_UID = ACC_TO_UID.get("WILBERT")
if not W_AT:
    raise SystemExit("❌ No tengo token Wilbert")

H_W = {"Authorization": f"Bearer {W_AT}"}
print(f"\n=== Bajando órdenes de WILBERT (uid {W_UID}) ===")

# Status del seller
me_w = requests.get("https://api.mercadolibre.com/users/me", headers=H_W, timeout=15).json()
print(f"  status: site_status={me_w.get('site_status')} status={(me_w.get('status') or {}).get('site_status')}")
print(f"  buyer_reputation: {me_w.get('buyer_reputation')}")
print(f"  seller_reputation: {me_w.get('seller_reputation')}")

orders = []
offset = 0
while True:
    r = requests.get(f"https://api.mercadolibre.com/orders/search?seller={W_UID}&limit=50&offset={offset}",
                     headers=H_W, timeout=20).json()
    res = r.get("results", [])
    if not res: break
    orders.extend(res)
    offset += len(res)
    if offset >= r.get("paging",{}).get("total",0): break
    if offset >= 500: break  # cap

print(f"  total órdenes: {len(orders)}")

# 3. Análisis de buyers + shipping + cross-check con otras cuentas
buyer_count = Counter()
buyer_nicks = {}
buyer_emails = {}
shipping_addrs = Counter()
buyer_ids_set = set()
items_sold = Counter()

for o in orders:
    b = o.get("buyer", {}) or {}
    bid = b.get("id")
    if bid:
        buyer_count[bid] += 1
        buyer_nicks[bid] = b.get("nickname","")
        buyer_emails[bid] = b.get("email","")
        buyer_ids_set.add(bid)
    sh = o.get("shipping", {}) or {}
    rec = sh.get("receiver_address", {}) or {}
    addr = f"{rec.get('zip_code','')}-{rec.get('city',{}).get('name','') if isinstance(rec.get('city'),dict) else ''}-{rec.get('state',{}).get('name','') if isinstance(rec.get('state'),dict) else ''}"
    if addr.strip("-"):
        shipping_addrs[addr] += 1
    for it in o.get("order_items", []):
        items_sold[it.get("item",{}).get("id","?")] += it.get("quantity",1)

print(f"\n=== BUYERS — top 20 ===")
for bid, n in buyer_count.most_common(20):
    print(f"  {bid:<12} {buyer_nicks.get(bid,'?'):<30} count={n}")

# 4. CROSS-CHECK: ¿alguno de estos buyers es ALSO un seller en alguna de mis cuentas?
print(f"\n=== CROSS-CHECK: buyers que son OTRAS cuentas mías ===")
my_uids = set(ACC_TO_UID.values())
for bid in buyer_ids_set:
    if bid in my_uids:
        which_acc = [a for a, u in ACC_TO_UID.items() if u == bid][0]
        print(f"  ⚠️  buyer_id {bid} = MI CUENTA {which_acc}!  (compró en Wilbert {buyer_count[bid]} veces)")

# 5. Buyers que aparecen ALSO como buyers en las otras cuentas
print(f"\n=== Buyers que también compran en otras cuentas mías ===")
buyers_per_acc = defaultdict(set)
for acc, at in ACC_TO_TOK.items():
    if acc == "WILBERT": continue
    H = {"Authorization": f"Bearer {at}"}
    uid = ACC_TO_UID[acc]
    offset = 0
    while True:
        r = requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&limit=50&offset={offset}",
                         headers=H, timeout=20).json()
        res = r.get("results", [])
        if not res: break
        for o in res:
            b = (o.get("buyer") or {}).get("id")
            if b: buyers_per_acc[acc].add(b)
        offset += len(res)
        if offset >= r.get("paging",{}).get("total",0): break
        if offset >= 500: break

shared_buyers = {}
for bid in buyer_ids_set:
    accs_with_bid = [a for a, bset in buyers_per_acc.items() if bid in bset]
    if accs_with_bid:
        shared_buyers[bid] = accs_with_bid

print(f"  Total buyers de Wilbert que también compraron en otras cuentas mías: {len(shared_buyers)}")
for bid, accs in sorted(shared_buyers.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  {bid} {buyer_nicks.get(bid,'?'):<30} — Wilbert + {','.join(accs)}")

# 6. Top códigos postales (¿muchas ventas al mismo CP?)
print(f"\n=== TOP códigos postales/destinos ===")
for addr, n in shipping_addrs.most_common(15):
    print(f"  {n:>4}  {addr}")

# 7. Reportar resumen
print(f"\n{'='*60}\n=== RESUMEN AUDITORÍA WILBERT ===\n{'='*60}")
print(f"Órdenes totales: {len(orders)}")
print(f"Buyers únicos: {len(buyer_ids_set)}")
print(f"Buyers compartidos con otras cuentas mías: {len(shared_buyers)}")
print(f"Top buyer (más compras): {buyer_count.most_common(1)}")

# Telegram
if TG and TGCID:
    msg = f"🔍 *Audit Wilbert (link MELI ban)*\n\n"
    msg += f"Órdenes: {len(orders)}\n"
    msg += f"Buyers únicos: {len(buyer_ids_set)}\n"
    msg += f"Buyers que también compraron en otras cuentas: *{len(shared_buyers)}*\n\n"
    if shared_buyers:
        msg += "Top buyers compartidos:\n"
        for bid, accs in sorted(shared_buyers.items(), key=lambda x: -len(x[1]))[:8]:
            msg += f"• `{buyer_nicks.get(bid,bid)}` → Wilbert + {','.join(accs)}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=15)
