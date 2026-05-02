#!/usr/bin/env python3
"""Cuenta paquetes ready_to_ship / ready_to_print por cuenta + total.
Manda resultado a Telegram.
"""
import os, json, requests, time

APP_ID     = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT    = os.environ["TELEGRAM_CHAT_ID"]

ACCOUNTS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "BREN":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "YC_NEW":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}

def refresh(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": APP_ID, "client_secret": APP_SECRET,
        "refresh_token": rt,
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def me(tok):
    return requests.get("https://api.mercadolibre.com/users/me",
                        headers={"Authorization": f"Bearer {tok}"}, timeout=20).json()

def count_orders(tok, uid, status="paid"):
    """Lista todos los orders pagados, agrupa por shipping substatus."""
    h = {"Authorization": f"Bearer {tok}"}
    by_status = {}
    by_sub = {}
    offset = 0
    total_orders = 0
    while True:
        r = requests.get(
            "https://api.mercadolibre.com/orders/search",
            headers=h,
            params={"seller": uid, "order.status": status,
                    "sort": "date_desc", "limit": 50, "offset": offset},
            timeout=30,
        )
        if r.status_code >= 400:
            print(f"  err orders: {r.status_code} {r.text[:120]}")
            break
        d = r.json()
        results = d.get("results", [])
        for o in results:
            ship = o.get("shipping", {})
            sid = ship.get("id")
            if not sid:
                by_status["sin_envio"] = by_status.get("sin_envio", 0) + 1
                continue
            # Get shipment detail
            try:
                sr = requests.get(
                    f"https://api.mercadolibre.com/shipments/{sid}",
                    headers=h, timeout=20,
                )
                if sr.status_code >= 400:
                    by_status["err_get"] = by_status.get("err_get", 0) + 1
                    continue
                s = sr.json()
                st = s.get("status", "?")
                ss = s.get("substatus", "")
                by_status[st] = by_status.get(st, 0) + 1
                key = f"{st}/{ss or '-'}"
                by_sub[key] = by_sub.get(key, 0) + 1
            except Exception as e:
                print(f"  shipment {sid} err: {e}")
        total_orders += len(results)
        if len(results) < 50 or offset > 500:
            break
        offset += 50
    return by_status, by_sub, total_orders

def main():
    summary = {}
    grand_ready = 0
    grand_handling = 0
    grand_total = 0

    for nick, rt in ACCOUNTS.items():
        if not rt:
            continue
        try:
            tok = refresh(rt)
            uid = me(tok).get("id")
        except Exception as e:
            print(f"{nick}: refresh fallo {e}")
            continue
        if not uid:
            continue
        print(f"\n=== {nick} (uid={uid}) ===")
        by_st, by_sub, total = count_orders(tok, uid, "paid")
        # MELI shipment statuses interesantes:
        # - ready_to_ship: etiqueta lista, esperando entrega a Mercado Envíos
        # - handling: orden creada, esperando preparación
        # - shipped: ya en camino
        # - pending: comprador pago, esperando que MELI procese
        ready = by_st.get("ready_to_ship", 0)
        handling = by_st.get("handling", 0)
        pending = by_st.get("pending", 0)
        shipped = by_st.get("shipped", 0)
        delivered = by_st.get("delivered", 0)

        print(f"  Total ord pagadas (recientes): {total}")
        print(f"  ready_to_ship (imprime etiqueta): {ready}")
        print(f"  handling (preparando): {handling}")
        print(f"  pending: {pending}")
        print(f"  shipped: {shipped}")
        print(f"  delivered: {delivered}")
        if by_sub:
            for k, v in sorted(by_sub.items(), key=lambda x: -x[1])[:6]:
                print(f"    sub: {k} = {v}")
        summary[nick] = {"ready": ready, "handling": handling,
                         "pending": pending, "shipped": shipped}
        grand_ready += ready
        grand_handling += handling
        grand_total += total

    # Mensaje TG
    lines = ["📦 <b>PAQUETES READY-TO-SHIP — " + time.strftime("%d/%m/%Y %H:%M") + "</b>", ""]
    lines.append("<i>(órdenes pagadas pendientes de imprimir etiqueta o preparar)</i>")
    lines.append("")

    for nick, d in summary.items():
        if d["ready"] + d["handling"] + d["pending"] == 0:
            continue
        lines.append(f"<b>{nick}</b>")
        if d["ready"]:    lines.append(f"  📍 Ready-to-ship: <b>{d['ready']}</b>")
        if d["handling"]: lines.append(f"  🔧 Handling:      <b>{d['handling']}</b>")
        if d["pending"]:  lines.append(f"  ⏳ Pending:       <b>{d['pending']}</b>")
        if d["shipped"]:  lines.append(f"  🚚 Shipped:       {d['shipped']}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🎯 <b>TOTAL pendientes etiqueta:</b> {grand_ready}")
    lines.append(f"🔧 <b>TOTAL en handling:</b>          {grand_handling}")

    msg = "\n".join(lines)
    print("\n" + msg)

    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "parse_mode": "HTML", "text": msg},
        timeout=20,
    )

if __name__ == "__main__":
    main()
