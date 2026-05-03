#!/usr/bin/env python3
"""Inspeccionar estructura de un shipment activo de Raymundo para encontrar
el path correcto al estimated_handling_limit."""
import os, requests, json
from datetime import datetime, timedelta, timezone

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
uid = me["id"]

# Ultima orden paid
NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=2)
r = requests.get("https://api.mercadolibre.com/orders/search",
    headers=H, timeout=20,
    params={"seller":uid, "order.status":"paid",
            "order.date_created.from":START.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "limit":3,"offset":0}).json()

for o in r.get("results",[])[:3]:
    sh = (o.get("shipping") or {}).get("id")
    if not sh: continue
    print(f"\n{'='*60}\n=== Shipment {sh} ===")
    sh_data = requests.get(f"https://api.mercadolibre.com/shipments/{sh}",
                          headers=H, timeout=10).json()
    # Solo campos relevantes para deadline
    print(f"status: {sh_data.get('status')}")
    print(f"substatus: {sh_data.get('substatus')}")
    print(f"date_created: {sh_data.get('date_created')}")
    print(f"date_first_printed: {sh_data.get('date_first_printed')}")
    print(f"shipping_mode: {sh_data.get('shipping_mode')}")
    print(f"logistic_type: {sh_data.get('logistic_type')}")
    # lead_time
    lt = sh_data.get("lead_time")
    print(f"\nlead_time keys: {list(lt.keys()) if lt else None}")
    if lt:
        for k,v in lt.items():
            print(f"  {k}: {json.dumps(v) if isinstance(v,(dict,list)) else v}")
    # status_history
    sh_hist = sh_data.get("status_history") or {}
    print(f"\nstatus_history keys: {list(sh_hist.keys())[:10]}")
    # Otros campos top-level relevantes
    for k in ["estimated_delivery","handling_time","delay","tracking_number","tracking_method"]:
        if k in sh_data:
            print(f"{k}: {json.dumps(sh_data[k]) if isinstance(sh_data[k],(dict,list)) else sh_data[k]}")
    # full dump truncado de lead_time
    print(f"\n--- FULL lead_time JSON ---")
    print(json.dumps(lt, indent=2, default=str)[:1500])
