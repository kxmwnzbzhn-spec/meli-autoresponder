"""
INVENTORY SYNC MASTER — Sincroniza stock master con todas las cuentas MELI.

Flujo cada N minutos:
1. Carga inventario_master.json
2. Recorre las 7 cuentas MELI y mapea cada item activo a (modelo, color)
3. Para cada item:
   - Si master_stock > 0: forzar available_quantity=1 (visible MELI)
   - Si master_stock == 0: pausar item (no más ventas)
4. Cuenta ventas nuevas desde último run y descuenta del master
5. Si master baja a 0, alerta Telegram + pausa

inventario_master.json estructura:
{
  "stock": {"JBL Go 4|Rojo": {"nuevo": 393, ...}, ...},
  "_categorize_keywords": {...},
  "_last_sync": "iso timestamp",
  "_consumed_orders": ["order_id1", ...] (para no doble-contar)
}
"""
import os, requests, json, time, re
from datetime import datetime, timezone, timedelta

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

ACCOUNTS = [
    ("JUAN","MELI_REFRESH_TOKEN"),
    ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
    ("YC_NEW","MELI_REFRESH_TOKEN_YC_NEW"),
    ("BREN","MELI_REFRESH_TOKEN_BREN"),
]

MASTER_FILE = "inventario_master.json"

def load_master():
    with open(MASTER_FILE) as f: return json.load(f)

def save_master(m):
    with open(MASTER_FILE,"w") as f: json.dump(m,f,indent=2,ensure_ascii=False)

master = load_master()
keywords = master.get("_categorize_keywords",{})

def categorize_item(title, var_attrs=None):
    """Retorna 'JBL Go 4|Aqua' o None."""
    t = (title or "").lower()
    if var_attrs:
        for a in var_attrs:
            if a.get("id")=="COLOR" or "color" in a.get("name","").lower():
                cv = (a.get("value_name","") or "").lower()
                t += " " + cv
    for key, kws in keywords.items():
        if any(kw in t for kw in kws):
            return key
    return None

# Auth all accounts
account_tokens = {}
for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
            data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
            timeout=15).json()
        me = requests.get("https://api.mercadolibre.com/users/me",
            headers={"Authorization":f"Bearer {r['access_token']}"},timeout=10).json()
        account_tokens[label] = {"token": r["access_token"], "user_id": me["id"], "nick": me.get("nickname","")}
    except Exception as e:
        print(f"[{label}] auth err: {e}")
print(f"Accounts auth: {len(account_tokens)}")

# === STEP 1: Decrement por ventas nuevas ===
last_sync = master.get("_last_sync")
consumed = set(master.get("_consumed_orders",[]))
since = last_sync or (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
date_from = since[:19] + ".000Z" if "T" in since else since
print(f"\nLast sync: {last_sync} → buscando ventas desde {date_from}")

decrements = {}  # key -> qty_sold
new_consumed = []

for label, info in account_tokens.items():
    H = {"Authorization":f"Bearer {info['token']}"}
    offset = 0
    while True:
        try:
            rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={info['user_id']}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
        except: break
        results = rr.get("results",[])
        if not results: break
        for o in results:
            oid = str(o.get("id"))
            if oid in consumed: continue
            if o.get("status") not in ("paid","shipped","delivered"): continue
            for oi in o.get("order_items",[]):
                title = (oi.get("item") or {}).get("title","")
                vattrs = (oi.get("item") or {}).get("variation_attributes") or []
                key = categorize_item(title, vattrs)
                qty = oi.get("quantity",0)
                if key and qty:
                    decrements[key] = decrements.get(key,0) + qty
                    new_consumed.append(oid)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

# Apply decrements
if decrements:
    print(f"\n💸 Descontando del master por ventas:")
    for key, qty in decrements.items():
        before = master["stock"].get(key,{}).get("nuevo",0)
        if key in master["stock"]:
            master["stock"][key]["nuevo"] = max(0, before - qty)
            master["stock"][key]["total"] = master["stock"][key]["nuevo"] + master["stock"][key].get("devolucion",0)
            print(f"  {key}: -{qty} → {master['stock'][key]['nuevo']}u")
        else:
            print(f"  {key}: -{qty} (NUEVO key, master desconocido)")
    consumed.update(new_consumed)
    master["_consumed_orders"] = list(consumed)[-5000:]  # keep last 5000

# === STEP 2: Sync each MELI item ===
print(f"\n🔄 Sincronizando items MELI con master...")
total_active=0; total_paused=0; total_qty_fixed=0
alerts = []

for label, info in account_tokens.items():
    H = {"Authorization":f"Bearer {info['token']}","Content-Type":"application/json"}
    USER_ID = info["user_id"]
    # Get all items
    ids = []; offset = 0
    for st in ("active","paused"):
        offset = 0
        while True:
            try:
                rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
            except: break
            b = rr.get("results",[])
            if not b: break
            ids.extend([(iid, st) for iid in b])
            offset += 50
            if offset >= rr.get("paging",{}).get("total",0): break
    
    for iid, st in ids:
        try:
            g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,available_quantity,catalog_listing,variations",headers=H,timeout=10).json()
        except: continue
        title = g.get("title","")
        qty = g.get("available_quantity",0)
        # Variations? sum stock by variation
        variations = g.get("variations") or []
        if variations:
            # Skip variation items for now (complex)
            continue
        
        key = categorize_item(title)
        if not key: continue
        
        master_stock = master["stock"].get(key,{}).get("total",0)
        if master_stock == 0:
            # Pausar item si tiene stock master=0
            if st == "active":
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
                if rp.status_code == 200:
                    total_paused += 1
                    print(f"  ⏸️ {label}/{iid} {key} → pausado (master=0)")
                    alerts.append(f"⏸️ {label} {iid} pausado: {key} sin stock")
        else:
            # Asegurar qty=1 visible
            if qty != 1:
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=15)
                if rp.status_code == 200:
                    total_qty_fixed += 1
            if st == "paused":
                # Reactivar si master tiene stock
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active","available_quantity":1},timeout=15)
                if rp.status_code == 200:
                    total_active += 1
                    print(f"  ▶️ {label}/{iid} {key} → reactivado")
        time.sleep(0.1)

master["_last_sync"] = datetime.now(timezone.utc).isoformat()
save_master(master)

print(f"\n=== RESUMEN ===")
print(f"  Ventas descontadas: {sum(decrements.values())}u en {len(decrements)} variantes")
print(f"  Items reactivados: {total_active}")
print(f"  Items pausados (master=0): {total_paused}")
print(f"  qty fixed→1: {total_qty_fixed}")

if alerts and TG_TOKEN and TG_CHAT:
    text = "📦 *Inventory Sync*\n" + "\n".join(alerts[:10])
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id":TG_CHAT,"text":text,"parse_mode":"Markdown"})
