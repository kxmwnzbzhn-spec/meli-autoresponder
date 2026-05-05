"""Saldo REAL Raymundo: bruto, comisión MELI, envíos, IVA/ISR retenidos,
descuentos/promos, y NETO LÍQUIDO (lo que efectivamente entra a MercadoPago).
Usa payments[].net_received_amount + shipments cost detail.
Periodo: lunes 27 abr → domingo 3 may 2026.
"""
import os, requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

TZ=timezone(timedelta(hours=-6))
START=datetime(2026,4,27,0,0,0,tzinfo=TZ)
END  =datetime(2026,5,4,0,0,0,tzinfo=TZ)
print(f"Semana Raymundo: {START.date()} → {(END-timedelta(days=1)).date()} CDMX")

r=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']} ({uid})\n")

# Saldo MercadoPago actual
print("--- SALDO MP ACTUAL ---")
try:
    bal=requests.get(f"https://api.mercadolibre.com/users/{uid}/mercadopago_account/balance",
                     headers=H,timeout=15).json()
    print(f"  raw: {bal}")
except Exception as e:
    print(f"  err: {e}")

print("\n--- ORDENES SEMANA ---")
orders=[]; offset=0
while True:
    rr=requests.get("https://api.mercadolibre.com/orders/search",headers=H,
        params={"seller":uid,
                "order.date_created.from":START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "order.date_created.to":  END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "limit":50,"offset":offset},timeout=20).json()
    res=rr.get("results",[])
    if not res: break
    orders.extend(res); offset+=len(res)
    if offset>=rr.get("paging",{}).get("total",0): break

paid=[o for o in orders if o.get("status")=="paid"]
print(f"orders fetched: {len(orders)}  paid={len(paid)}")

bruto=0.0
comision_meli=0.0
shipping_seller=0.0   # lo que paga el seller en envíos (free shipping)
taxes_retenidos=0.0   # IVA/ISR retenidos
descuentos=0.0        # promociones, MELI Ads
neto_mp=0.0           # net_received_amount sumado de todos los payments
units=0
canc=0

by_model=defaultdict(lambda:{"u":0,"$":0.0})
shipping_detail=[]

for o in paid:
    units_o=sum(it.get("quantity",1) for it in o.get("order_items",[]))
    units+=units_o
    line_gross=0.0
    for it in o.get("order_items",[]):
        qty=it.get("quantity",1)
        up=float(it.get("unit_price",0) or 0)
        sf=float(it.get("sale_fee",0) or 0)
        bruto+=up*qty
        comision_meli+=sf*qty
        line_gross+=up*qty
        t=(it.get("item",{}).get("title","") or "").lower()
        if   "go 4" in t or "go4" in t: m="Go 4"
        elif "go 3" in t or "go3" in t: m="Go 3"
        elif "clip 5" in t or "clip5" in t: m="Clip 5"
        elif "charge" in t: m="Charge 6"
        elif "flip" in t: m="Flip 7"
        elif "grip" in t: m="Grip"
        elif "bose" in t or "soundlink" in t: m="Bose"
        elif "sony" in t or "xb100" in t: m="Sony"
        else: m="Otros"
        by_model[m]["u"]+=qty
        by_model[m]["$"]+=up*qty
    # Payments → taxes retenidos + net_received
    for p in o.get("payments",[]):
        try:
            ta=float(p.get("taxes_amount") or 0)
            sc=float(p.get("shipping_cost") or 0)
            nr=float(p.get("net_received_amount") or 0)
            mfee=float(p.get("marketplace_fee") or 0)
        except: ta=sc=nr=mfee=0
        taxes_retenidos+=ta
        neto_mp+=nr
    # Coupon / promo at order level
    coup=float(o.get("coupon",{}).get("amount") or 0)
    descuentos+=coup

# Para shipping seller cost: pegar a /shipments/{id}/costs por cada shipment único
# (lento, hacerlo solo si quieres detalle preciso). Hoy: estimar via free_shipping flag
print(f"\n  Pegando a /shipments/.../costs para envíos seller...")
ship_ids=set()
for o in paid:
    sid=(o.get("shipping") or {}).get("id")
    if sid: ship_ids.add(sid)
print(f"  shipments únicos: {len(ship_ids)}")

# Sample first 100 to estimate, then extrapolate (full would be too slow)
sampled=list(ship_ids)[:200]
ship_cost_sample=0.0
ship_cost_total_known=0.0
ship_count_with_cost=0
for sid in sampled:
    try:
        sc=requests.get(f"https://api.mercadolibre.com/shipments/{sid}/costs",headers=H,timeout=8).json()
        # sender es el seller normalmente
        sender=sc.get("senders",[{}])[0]
        cost=float(sender.get("cost") or 0)
        comp=float(sender.get("compensation") or 0)
        seller_pays=cost-comp
        if seller_pays != 0:
            ship_cost_sample+=seller_pays
            ship_count_with_cost+=1
    except Exception as e:
        pass
avg_ship=ship_cost_sample/len(sampled) if sampled else 0
shipping_seller=avg_ship*len(ship_ids)
print(f"  promedio envío/shipment (sample {len(sampled)}): ${avg_ship:.2f}")
print(f"  shipping_seller estimado total: ${shipping_seller:,.0f}")

# NETO LÍQUIDO REAL
neto_liquido = neto_mp - shipping_seller - descuentos

print(f"\n{'='*60}")
print(f"=== SALDO REAL RAYMUNDO — SEMANA 27/04 - 03/05 ===")
print(f"{'='*60}")
print(f"BRUTO            : ${bruto:,.0f}")
print(f"  -comisión MELI : -${comision_meli:,.0f}")
print(f"  -IVA/ISR reten : -${taxes_retenidos:,.0f}")
print(f"  -envíos seller : -${shipping_seller:,.0f}  (estimado)")
print(f"  -descuentos    : -${descuentos:,.0f}")
print(f"-"*60)
print(f"  net_received_MP: ${neto_mp:,.0f}  (lo que entra a MercadoPago)")
print(f"  - envíos       : -${shipping_seller:,.0f}")
print(f"-"*60)
print(f"  NETO LÍQUIDO   : ${neto_liquido:,.0f}")
print(f"\n  (ordenes paid: {len(paid)}  units: {units})")

if TG and TGCID:
    msg=f"💰 *RAYMUNDO — SALDO REAL Semana 27/04-03/05*\n\n"
    msg+=f"Bruto: ${bruto:,.0f}\n"
    msg+=f"  − Comisión MELI: ${comision_meli:,.0f}\n"
    msg+=f"  − IVA/ISR retenido: ${taxes_retenidos:,.0f}\n"
    msg+=f"  − Envíos seller: ~${shipping_seller:,.0f}\n"
    msg+=f"  − Descuentos: ${descuentos:,.0f}\n"
    msg+=f"\n*Net received MP: ${neto_mp:,.0f}*\n"
    msg+=f"− envíos: ${shipping_seller:,.0f}\n"
    msg+=f"\n💵 *NETO LÍQUIDO: ${neto_liquido:,.0f}*\n"
    msg+=f"\n_{units}u en {len(paid)} órdenes_"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]},timeout=20)
    print("\n✅ Telegram enviado")
