"""Recupera etiquetas de Rocio impresas por primera vez hoy y las consolida."""
import os
import time
from datetime import datetime, timedelta, timezone
import requests

import daily_run as d


def printed_today(shipment):
    """En recuperación, acepta todo envío que aún siga listo para despachar."""
    return shipment.get("status") == "ready_to_ship"


def collect_rocio(access_token, account):
    headers = {"Authorization": f"Bearer {access_token}"}
    uid = account["expected_uid"]
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=180)
    orders = []
    offset = 0
    while True:
        response = requests.get(
            "https://api.mercadolibre.com/orders/search",
            headers=headers,
            timeout=20,
            params={
                "seller": uid,
                "order.status": "paid",
                "order.date_created.from": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit": 50,
                "offset": offset,
            },
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("results", [])
        if not batch:
            break
        orders.extend(batch)
        offset += len(batch)
        if offset >= payload.get("paging", {}).get("total", 0):
            break

    by_shipment = {}
    for order in orders:
        shipment_id = (order.get("shipping") or {}).get("id")
        if shipment_id:
            by_shipment.setdefault(shipment_id, []).append(order)

    selected = []
    for shipment_id, shipment_orders in by_shipment.items():
        try:
            shipment_response = requests.get(
                f"https://api.mercadolibre.com/shipments/{shipment_id}",
                headers=headers,
                timeout=12,
            )
            shipment_response.raise_for_status()
            shipment = shipment_response.json()
            if shipment.get("status") != "ready_to_ship" or not printed_today(shipment):
                continue

            lines = []
            has_used = False
            for order in shipment_orders:
                for order_item in order.get("order_items", []):
                    item = order_item.get("item") or {}
                    clean, _ = d.clean_title(item, headers)
                    quantity = order_item.get("quantity", 1)
                    condition = d.get_condition(item, headers)
                    if condition == "used":
                        has_used = True
                        lines.append(f"USADO {quantity} {clean}")
                    else:
                        lines.append(f"{quantity} {clean}")
            if not lines:
                continue
            buyer = (shipment_orders[0].get("buyer") or {}).get("nickname", "?")
            selected.append({
                "sid": shipment_id,
                "account": "RocioAngel",
                "buyer": buyer,
                "comp_lines": lines,
                "has_used": has_used,
                "n_prods": len(lines),
                "at": access_token,
            })
            time.sleep(0.04)
        except Exception as exc:
            print(f"WARN shipment {shipment_id}: {exc}", flush=True)

    selected.sort(key=lambda item: (
        0 if item["has_used"] else 1,
        "/".join(item["comp_lines"]),
        item["sid"],
    ))
    return selected


def main():
    account = next(a for a in d.ACCOUNTS if a["name"] == "RocioAngel")
    access_token, error = d.validate_account(account)
    if error:
        raise RuntimeError(error)
    shipments = collect_rocio(access_token, account)
    output = f"ETIQUETAS_ROCIOANGEL_{d.TODAY}.pdf"
    pages, failures = d.build_pdf(shipments, output)
    print(f"RECOVERED={len(shipments)} PAGES={pages} FAILURES={len(failures)} FILE={output}")
    if pages == 0 or failures:
        raise RuntimeError(f"PDF incompleto: pages={pages}, failures={failures}")


if __name__ == "__main__":
    main()
