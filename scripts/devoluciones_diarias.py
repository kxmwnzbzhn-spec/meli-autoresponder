"""Reporte diario de devoluciones recibidas hoy en cada cuenta MELI.
Cron: 22:00 CDMX. Tira por Telegram el conteo por cuenta.
"""
import os, requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import meli_token

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "Juan":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "Claribel": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "Asva":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "Raymundo": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "Dilcie":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "Mildred":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "Bren":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "Wilbert":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
}

TZ=timezone(timedelta(hours=-6))
TODAY=datetime.now(TZ).date()
START=datetime(TODAY.year,TODAY.month,TODAY.day,0,0,0,tzinfo=TZ)
END  =START+timedelta(days=1)
print(f"Devoluciones hoy: {TODAY} CDMX")

def tok(rt):
    r=meli_token.refresh(rt).json()
    return r.get("access_token")

results = {}
total = 0
detail_by_acc = {}

for acc, rt in ACCS.items():
    if not rt:
        results[acc] = None
        continue
    at = tok(rt)
    if not at:
        results[acc] = None
        continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid:
        results[acc] = None
        continue

    # /post-purchase/v1/claims/search?stage=claim&type=mediation&status=opened (returns con shipping)
    # Más confiable: /orders/search con tag=return o filtrar status=cancelled con shipping returning
    # MELI returns: /shipments/search?status=delivered_to_sender (entrega devuelta al vendedor)
    count = 0
    items_detail = []

    # Buscar shipments con status que indique devolución entregada hoy
    # status: 'delivered_to_sender' → devolución entregada al seller
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.mercadolibre.com/shipments/search",
                headers=H,
                params={
                    "seller": uid,
                    "shipping.status": "delivered_to_sender",
                    "shipping.last_updated.from": START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "shipping.last_updated.to":   END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit": 50, "offset": offset,
                },
                timeout=20,
            ).json()
        except Exception as e:
            print(f"  {acc}: err shipments {e}")
            break
        res = r.get("results", [])
        if not res:
            break
        count += len(res)
        for s in res:
            items_detail.append({
                "shipment_id": s.get("id"),
                "tracking": s.get("tracking_number"),
                "last_updated": s.get("last_updated"),
            })
        offset += len(res)
        if offset >= r.get("paging", {}).get("total", 0):
            break

    # Fallback / complementario: claims abiertos hoy (alternativa)
    # /post-purchase/v1/claims/search?status=opened&date_created.from=...
    claims_count = 0
    try:
        rc = requests.get(
            "https://api.mercadolibre.com/post-purchase/v1/claims/search",
            headers=H,
            params={
                "stage": "claim",
                "status": "opened",
                "date_created.from": START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "date_created.to":   END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            },
            timeout=15,
        ).json()
        claims_count = rc.get("paging", {}).get("total", 0) or len(rc.get("data", []) or [])
    except Exception as e:
        pass

    results[acc] = {"devoluciones_recibidas": count, "claims_hoy": claims_count}
    detail_by_acc[acc] = items_detail
    total += count
    print(f"  {acc}: devoluciones={count}  claims={claims_count}")

print(f"\nTOTAL devoluciones recibidas hoy: {total}")

if TG and TGCID:
    msg = f"📦 *DEVOLUCIONES HOY {TODAY.strftime('%d/%m/%Y')}*\n\n"
    msg += f"*TOTAL: {total} paquetes devueltos*\n\n"
    for acc in ACCS:
        s = results.get(acc)
        if s is None:
            continue
        d = s["devoluciones_recibidas"]
        c = s["claims_hoy"]
        line = f"• {acc}: *{d}* devoluciones"
        if c:
            line += f"  _(claims: {c})_"
        msg += line + "\n"
    requests.post(
        f"https://api.telegram.org/bot{TG}/sendMessage",
        data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
        timeout=20,
    )
    print("\n✅ Telegram enviado")
