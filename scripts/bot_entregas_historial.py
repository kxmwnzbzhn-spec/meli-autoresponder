"""Reporte diario del bot de entregas.
Pega al endpoint /api/deliveries del bot, filtra las de HOY (CDMX),
compila CSV y manda resumen a Telegram.
"""
import os, csv, requests, io
from datetime import datetime, timedelta, timezone
from collections import defaultdict

BOT_URL = os.environ.get("BOT_URL", "https://elitemarket-chatbot-production.up.railway.app")
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

TZ = timezone(timedelta(hours=-6))
TODAY = datetime.now(TZ).date()
TODAY_STR = TODAY.isoformat()
START = datetime(TODAY.year, TODAY.month, TODAY.day, 0, 0, 0, tzinfo=TZ)
END = START + timedelta(days=1)

print(f"Día: {TODAY_STR}")
print(f"Range: {START.isoformat()} → {END.isoformat()}")

# Bajar todas las deliveries del bot
try:
    r = requests.get(f"{BOT_URL}/api/deliveries", timeout=15)
    data = r.json()
    deliveries_all = data.get("deliveries", [])
except Exception as e:
    print(f"❌ Error fetch /api/deliveries: {e}")
    deliveries_all = []

print(f"Total deliveries en bot: {len(deliveries_all)}")

# Filtrar solo las de HOY
def in_today(d):
    started = d.get("startedAt", "")
    if not started:
        return False
    try:
        dt = datetime.fromisoformat(started.replace("Z", "+00:00")).astimezone(TZ)
        return START <= dt < END
    except:
        return False

deliveries = [d for d in deliveries_all if in_today(d)]
print(f"Deliveries HOY: {len(deliveries)}")

# Construir filas del CSV
rows = []
total_packages = 0
done_count = 0
by_account = defaultdict(lambda: {"sesiones": 0, "completadas": 0, "paquetes": 0})
by_phone = defaultdict(lambda: {"sesiones": 0, "completadas": 0, "paquetes": 0})

for d in deliveries:
    phone = d.get("phone", "?")
    accounts = d.get("accounts", []) or []
    accounts_str = ",".join(accounts) if accounts else "(ninguna)"
    pkg = d.get("packageCount") or 0
    state = d.get("state", "incompleto")
    started = d.get("startedAt", "")
    completed = d.get("completedAt", "")
    geo = (d.get("geo") or {}).get("ok", False)
    has_photo = bool(d.get("photoPaquetes"))
    photo_path = (d.get("photoPaquetes") or {}).get("savedPath", "")
    location = d.get("location") or {}
    loc_str = f"{location.get('lat','')},{location.get('lng','')}" if location else ""

    is_done = state == "DONE"
    if is_done:
        done_count += 1
        total_packages += int(pkg or 0)

    rows.append({
        "fecha": TODAY_STR,
        "phone": phone,
        "cuentas": accounts_str,
        "paquetes": pkg,
        "estado": "ENTREGADO" if is_done else f"ABANDONO ({state})",
        "ubicacion_ok": "SI" if geo else "NO",
        "ubicacion": loc_str,
        "tiene_foto": "SI" if has_photo else "NO",
        "foto_path": photo_path,
        "iniciado": started,
        "completado": completed,
        "delivery_id": d.get("id", ""),
    })

    by_phone[phone]["sesiones"] += 1
    if is_done:
        by_phone[phone]["completadas"] += 1
        by_phone[phone]["paquetes"] += int(pkg or 0)
    for acc in accounts:
        by_account[acc]["sesiones"] += 1
        if is_done:
            by_account[acc]["completadas"] += 1
            by_account[acc]["paquetes"] += int(pkg or 0)

# Generar CSV
csv_path = f"data/bot_entregas_history/{TODAY_STR}.csv"
os.makedirs(os.path.dirname(csv_path), exist_ok=True)
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    if rows:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    else:
        f.write("# Sin deliveries hoy\n")

print(f"\nCSV guardado: {csv_path}")
print(f"Sesiones totales: {len(deliveries)}")
print(f"Completadas: {done_count}")
print(f"Total paquetes confirmados: {total_packages}")

print(f"\nPor cuenta:")
for acc, s in sorted(by_account.items()):
    print(f"  {acc}: {s['completadas']}/{s['sesiones']} sesiones, {s['paquetes']} paquetes")

print(f"\nPor repartidor:")
for p, s in sorted(by_phone.items()):
    print(f"  {p}: {s['completadas']}/{s['sesiones']} sesiones, {s['paquetes']} paquetes")

# Telegram
if TG and TGCID:
    msg = f"📦 *Bot Entregas — {TODAY.strftime('%d/%m/%Y')}*\n\n"
    msg += f"Sesiones iniciadas: *{len(deliveries)}*\n"
    msg += f"Completadas: *{done_count}*\n"
    msg += f"Paquetes confirmados: *{total_packages}*\n"
    if by_account:
        msg += f"\n*Por cuenta:*\n"
        for acc, s in sorted(by_account.items(), key=lambda x: -x[1]["paquetes"]):
            msg += f"• {acc}: {s['paquetes']} pkg ({s['completadas']}/{s['sesiones']})\n"
    if by_phone:
        msg += f"\n*Repartidores:*\n"
        for p, s in sorted(by_phone.items(), key=lambda x: -x[1]["paquetes"]):
            msg += f"• {p}: {s['paquetes']} pkg ({s['completadas']}/{s['sesiones']})\n"
    if not deliveries:
        msg += "\n_Hoy no se registraron sesiones._"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
                  timeout=15)
    print("\n✅ Telegram enviado")
