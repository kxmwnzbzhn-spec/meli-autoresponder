"""Cierre semanal lunes a domingo (CDMX). Esta semana: 27 abril - 3 mayo 2026."""
import os, requests, time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

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
}

TZ=timezone(timedelta(hours=-6))
TODAY=datetime.now(TZ).date()
# Semana lunes-domingo: hoy es domingo 3 mayo. Lunes = today - 6 days
SUN=TODAY  # domingo
MON=TODAY - timedelta(days=6)
START=datetime(MON.year,MON.month,MON.day,0,0,0,tzinfo=TZ)
END=datetime(SUN.year,SUN.month,SUN.day,0,0,0,tzinfo=TZ)+timedelta(days=1)
print(f"Semana: {MON} → {SUN} CDMX")
print(f"Range UTC: {START.astimezone(timezone.utc)} → {END.astimezone(timezone.utc)}\n")

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

def fetch_orders(H, uid):
    out=[]; offset=0
    while True:
        r=requests.get("https://api.mercadolibre.com/orders/search",headers=H,timeout=20,
            params={"seller":uid,
                    "order.date_created.from":START.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "order.date_created.to":END.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit":50,"offset":offset}).json()
        res=r.get("results",[])
        if not res: break
        out.extend(res)
        offset+=len(res)
        if offset >= r.get("paging",{}).get("total",0): break
    return out

# By day, by acc, by model
totals = defaultdict(lambda: {"orders":0,"u":0,"bruto":0.0,"comision":0.0,"neto":0.0,"canc":0})
day_totals = defaultdict(lambda: {"u":0,"neto":0.0})
acc_models = defaultdict(lambda: defaultdict(lambda: {"u":0,"$":0.0}))

for acc, rt in ACCS.items():
    if not rt: continue
    print(f"\n=== {acc} ===")
    at=tok(rt)
    if not at: continue
    H={"Authorization":f"Bearer {at}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=15).json()
    uid=me.get("id")
    if not uid: continue
    orders=fetch_orders(H,uid)
    paid=[o for o in orders if o.get("status")=="paid"]
    canc=[o for o in orders if o.get("status")=="cancelled"]
    print(f"  paid={len(paid)} canc={len(canc)}")

    for o in paid:
        # Day
        dc = o.get("date_created","")
        try:
            day = datetime.fromisoformat(dc.replace("Z","+00:00")).astimezone(TZ).date().isoformat()
        except:
            day = "?"
        for it in o.get("order_items",[]):
            qty=it.get("quantity",1)
            up=float(it.get("unit_price",0) or 0)
            sf=float(it.get("sale_fee",0) or 0)
            line=up*qty
            line_fee=sf*qty
            totals[acc]["bruto"] += line
            totals[acc]["comision"] += line_fee
            totals[acc]["u"] += qty
            day_totals[day]["u"] += qty
            day_totals[day]["neto"] += (line - line_fee)
            t=(it.get("item",{}).get("title","") or "").lower()
            if "go 4" in t or "go4" in t: m="Go 4"
            elif "go 3" in t or "go3" in t: m="Go 3"
            elif "clip 5" in t or "clip5" in t: m="Clip 5"
            elif "charge" in t: m="Charge 6"
            elif "flip" in t: m="Flip 7"
            elif "grip" in t: m="Grip"
            elif "perfum" in t or "edp" in t or "edt" in t: m="Perfumes"
            elif "sony" in t or "xb100" in t: m="Sony"
            elif "bose" in t or "soundlink" in t: m="Bose"
            else: m="Otros"
            acc_models[acc][m]["u"] += qty
            acc_models[acc][m]["$"] += line
        totals[acc]["orders"] += 1
    totals[acc]["canc"] = len(canc)
    totals[acc]["neto"] = totals[acc]["bruto"] - totals[acc]["comision"]
    print(f"  bruto=${totals[acc]['bruto']:,.0f} comision=${totals[acc]['comision']:,.0f} NETO=${totals[acc]['neto']:,.0f}")

# Print resumen
print(f"\n{'='*70}\n=== RESUMEN SEMANA {MON} → {SUN} ===")
total_neto=total_bruto=total_u=total_orders=total_canc=0
for acc in ACCS:
    s = totals[acc]
    if s["orders"] == 0 and s["canc"] == 0: continue
    print(f"\n{acc}: {s['orders']} orders, {s['u']}u, bruto ${s['bruto']:,.0f}, comision ${s['comision']:,.0f}, NETO ${s['neto']:,.0f}, canc {s['canc']}")
    for m, d in sorted(acc_models[acc].items(), key=lambda x: -x[1]["$"]):
        if d["u"]: print(f"  {m}: {d['u']}u  ${d['$']:,.0f}")
    total_orders += s["orders"]
    total_canc += s["canc"]
    total_u += s["u"]
    total_bruto += s["bruto"]
    total_neto += s["neto"]

print(f"\n{'='*60}")
print(f"TOTAL SEMANA: {total_orders} orders, {total_u}u")
print(f"  Bruto: ${total_bruto:,.0f}")
print(f"  Neto:  ${total_neto:,.0f}")
print(f"  Canc:  {total_canc}")

print(f"\n=== POR DÍA ===")
for day in sorted(day_totals.keys()):
    print(f"  {day}: {day_totals[day]['u']}u  NETO ${day_totals[day]['neto']:,.0f}")

if TG and TGCID:
    msg=f"📊 *CIERRE SEMANAL {MON.strftime('%d/%m')} - {SUN.strftime('%d/%m/%Y')}*\n\n"
    msg+=f"*TOTAL NETO: ${total_neto:,.0f}*\n"
    msg+=f"Bruto: ${total_bruto:,.0f}\n"
    msg+=f"Comisión MELI: -${(total_bruto-total_neto):,.0f}\n"
    msg+=f"Unidades: *{total_u}u* en {total_orders} ordenes\n"
    if total_canc: msg+=f"Canceladas: {total_canc}\n"
    msg+=f"\n*Por cuenta:*\n"
    for acc in ACCS:
        s=totals[acc]
        if s["orders"]==0 and s["canc"]==0: continue
        msg+=f"• {acc}: {s['u']}u → *${s['neto']:,.0f}*\n"
    msg+=f"\n*Por día:*\n"
    for day in sorted(day_totals.keys()):
        msg+=f"• {day[5:]}: {day_totals[day]['u']}u ${day_totals[day]['neto']:,.0f}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]},timeout=20)
