#!/usr/bin/env python3
"""Construye XLSX contabilidad MELI con todas las hojas + gráficas."""
import os, requests, json, sys
from datetime import datetime, timezone, timedelta
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import LineChart, BarChart, PieChart, Reference, BarChart3D
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "contabilidad_meli.xlsx"

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

# Compute date range (default: today CDMX so far; can override via DATE_FROM/DATE_TO)
date_str_arg = os.environ.get("ACCOUNTING_DATE")  # YYYY-MM-DD CDMX
if date_str_arg:
    target = datetime.strptime(date_str_arg, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=-6)))
else:
    target = datetime.now(timezone.utc) - timedelta(hours=6)

day_start_cdmx = target.replace(hour=0, minute=0, second=0, microsecond=0)
day_end_cdmx = day_start_cdmx + timedelta(days=1)
day_start_utc = day_start_cdmx.astimezone(timezone.utc)
day_end_utc = day_end_cdmx.astimezone(timezone.utc)
date_label = day_start_cdmx.strftime("%Y-%m-%d")

date_from = day_start_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
date_to = day_end_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# ====== Collect data from MELI ======
print(f"Collecting data for {date_label} CDMX")
print(f"  UTC: {date_from} → {date_to}")

per_account = {}
all_products = {}
all_returns = []

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var,"")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"[{label}] err: {e}"); continue
    
    a_orders = a_qty = 0
    a_bruto = a_fees = a_ship = 0
    a_returns_count = 0
    a_returns_amt = 0
    
    offset = 0
    while True:
        rr = requests.get(
            f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&order.date_created.to={date_to}&limit=50&offset={offset}",
            headers=H, timeout=20
        ).json()
        results = rr.get("results",[])
        if not results: break
        for o in results:
            st = o.get("status","")
            order_id = o.get("id")
            amt = o.get("total_amount",0) or 0
            
            # DEVOLUCIÓN REAL = paid + refunded, NO cancelled sin pago
            had_paid_payment = False
            real_refund_amt = 0
            for pay in o.get("payments",[]):
                if pay.get("status") == "approved":
                    had_paid_payment = True
                if pay.get("status") in ("refunded","charged_back"):
                    real_refund_amt += (pay.get("transaction_amount",0) or 0)
            
            if st == "cancelled" and not had_paid_payment:
                continue  # no es venta ni devolución
            
            if real_refund_amt > 0:
                a_returns_count += 1
                a_returns_amt += real_refund_amt
                items_o = o.get("order_items",[])
                prod = items_o[0].get("item",{}).get("title","")[:60] if items_o else ""
                all_returns.append({
                    "date": date_label, "account": label, "order_id": order_id,
                    "product": prod, "amount": real_refund_amt, "reason": "refunded"
                })
                if real_refund_amt >= amt: continue
                amt = amt - real_refund_amt
            
            if st not in ("paid","shipped","delivered"): continue
            a_orders += 1
            a_bruto += amt
            
            # Get fees from order detail
            try:
                od = requests.get(f"https://api.mercadolibre.com/orders/{order_id}",headers=H,timeout=10).json()
                for pay in od.get("payments",[]):
                    if pay.get("status") == "approved":
                        a_fees += (pay.get("marketplace_fee",0) or 0)
                sh_id = od.get("shipping",{}).get("id")
                if sh_id:
                    sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
                    so = sd.get("shipping_option",{}) or {}
                    list_cost = so.get("list_cost",0) or 0
                    cost_buyer = so.get("cost",0) or 0
                    a_ship += max(0, list_cost - cost_buyer)
            except: pass
            
            # Top products
            for oi in o.get("order_items",[]):
                qty = oi.get("quantity",0)
                a_qty += qty
                title = oi.get("item",{}).get("title","")[:60] or "?"
                key = (title, label)
                if key not in all_products:
                    all_products[key] = {"qty":0, "revenue":0}
                all_products[key]["qty"] += qty
                all_products[key]["revenue"] += qty * (oi.get("unit_price",0) or 0)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    a_iva = a_bruto - (a_bruto / 1.16) if a_bruto > 0 else 0
    a_net = a_bruto - a_fees - a_ship
    a_net_after_iva = a_net - a_iva
    
    per_account[label] = {
        "nickname": me.get("nickname",""),
        "orders": a_orders, "qty": a_qty, "bruto": a_bruto,
        "fees": a_fees, "ship": a_ship, "iva": a_iva,
        "returns_count": a_returns_count, "returns_amt": a_returns_amt,
        "net": a_net, "net_after_iva": a_net_after_iva
    }
    print(f"  {label}: {a_orders} ord / {a_qty}u / ${a_bruto:.0f} bruto")

# ====== Build XLSX ======
print(f"\nBuilding XLSX: {OUTPUT}")

# Load existing or create new
import os
if os.path.exists(OUTPUT):
    wb = load_workbook(OUTPUT)
    print("  Loaded existing workbook")
else:
    wb = Workbook()
    # Remove default sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    print("  Created new workbook")

# Style helpers
HDR_FILL = PatternFill("solid", start_color="1F4E78")
HDR_FONT = Font(bold=True, color="FFFFFF", name="Arial", size=11)
SUBT_FILL = PatternFill("solid", start_color="D9E1F2")
NUM_FMT = '"$"#,##0.00;[Red]("$"#,##0.00);"-"'
INT_FMT = '#,##0;[Red](#,##0);"-"'
PCT_FMT = '0.0%;[Red](0.0%);"-"'
BORDER = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

def style_header(cell):
    cell.fill = HDR_FILL; cell.font = HDR_FONT
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = BORDER

# ====== Sheet 1: Resumen Diario ======
sheet_name = "Resumen Diario"
if sheet_name in wb.sheetnames:
    s1 = wb[sheet_name]
else:
    s1 = wb.create_sheet(sheet_name)
    # Headers
    headers = ["Fecha", "Órdenes", "Unidades", "Bruto", "Comisión MELI", "Envío Seller", 
               "IVA Remite", "Devoluciones $", "Devoluciones #", "NET (sin IVA)", "NET (post IVA)", "Margen %"]
    for col, h in enumerate(headers, 1):
        c = s1.cell(row=1, column=col, value=h)
        style_header(c)
    s1.row_dimensions[1].height = 30
    for col in range(1, len(headers)+1):
        s1.column_dimensions[get_column_letter(col)].width = 14
    s1.column_dimensions['A'].width = 12

# Compute totals
t_orders = sum(d["orders"] for d in per_account.values())
t_qty = sum(d["qty"] for d in per_account.values())
t_bruto = sum(d["bruto"] for d in per_account.values())
t_fees = sum(d["fees"] for d in per_account.values())
t_ship = sum(d["ship"] for d in per_account.values())
t_iva = sum(d["iva"] for d in per_account.values())
t_ret_amt = sum(d["returns_amt"] for d in per_account.values())
t_ret_cnt = sum(d["returns_count"] for d in per_account.values())
t_net = t_bruto - t_fees - t_ship
t_net_after_iva = t_net - t_iva

# Find or create row for date_label
target_row = None
for row in range(2, s1.max_row + 1):
    if s1.cell(row=row, column=1).value == date_label:
        target_row = row
        break
if target_row is None:
    target_row = s1.max_row + 1 if s1.max_row > 1 else 2

s1.cell(row=target_row, column=1, value=date_label)
s1.cell(row=target_row, column=2, value=t_orders).number_format = INT_FMT
s1.cell(row=target_row, column=3, value=t_qty).number_format = INT_FMT
s1.cell(row=target_row, column=4, value=t_bruto).number_format = NUM_FMT
s1.cell(row=target_row, column=5, value=t_fees).number_format = NUM_FMT
s1.cell(row=target_row, column=6, value=t_ship).number_format = NUM_FMT
s1.cell(row=target_row, column=7, value=t_iva).number_format = NUM_FMT
s1.cell(row=target_row, column=8, value=t_ret_amt).number_format = NUM_FMT
s1.cell(row=target_row, column=9, value=t_ret_cnt).number_format = INT_FMT
s1.cell(row=target_row, column=10, value=f"=D{target_row}-E{target_row}-F{target_row}").number_format = NUM_FMT
s1.cell(row=target_row, column=11, value=f"=J{target_row}-G{target_row}").number_format = NUM_FMT
s1.cell(row=target_row, column=12, value=f"=IFERROR(K{target_row}/D{target_row},0)").number_format = PCT_FMT

# ====== Sheet 2: Detalle por Cuenta ======
sheet_name = "Detalle por Cuenta"
if sheet_name in wb.sheetnames:
    s2 = wb[sheet_name]
else:
    s2 = wb.create_sheet(sheet_name)
    headers = ["Fecha", "Cuenta", "Nickname", "Órdenes", "Unidades", "Bruto", "Comisión", 
               "Envío", "IVA", "Devoluciones $", "NET", "Margen %"]
    for col, h in enumerate(headers, 1):
        c = s2.cell(row=1, column=col, value=h)
        style_header(c)
    s2.row_dimensions[1].height = 30
    for col in range(1, len(headers)+1):
        s2.column_dimensions[get_column_letter(col)].width = 13
    s2.column_dimensions['A'].width = 12
    s2.column_dimensions['B'].width = 11
    s2.column_dimensions['C'].width = 18

# Remove existing rows for this date
rows_to_delete = []
for row in range(2, s2.max_row + 1):
    if s2.cell(row=row, column=1).value == date_label:
        rows_to_delete.append(row)
for r in reversed(rows_to_delete):
    s2.delete_rows(r)

# Append per-account
next_row = s2.max_row + 1 if s2.max_row > 1 else 2
for label, d in per_account.items():
    if d["orders"] == 0 and d["returns_count"] == 0: continue
    s2.cell(row=next_row, column=1, value=date_label)
    s2.cell(row=next_row, column=2, value=label)
    s2.cell(row=next_row, column=3, value=d["nickname"])
    s2.cell(row=next_row, column=4, value=d["orders"]).number_format = INT_FMT
    s2.cell(row=next_row, column=5, value=d["qty"]).number_format = INT_FMT
    s2.cell(row=next_row, column=6, value=d["bruto"]).number_format = NUM_FMT
    s2.cell(row=next_row, column=7, value=d["fees"]).number_format = NUM_FMT
    s2.cell(row=next_row, column=8, value=d["ship"]).number_format = NUM_FMT
    s2.cell(row=next_row, column=9, value=d["iva"]).number_format = NUM_FMT
    s2.cell(row=next_row, column=10, value=d["returns_amt"]).number_format = NUM_FMT
    s2.cell(row=next_row, column=11, value=f"=F{next_row}-G{next_row}-H{next_row}").number_format = NUM_FMT
    s2.cell(row=next_row, column=12, value=f"=IFERROR(K{next_row}/F{next_row},0)").number_format = PCT_FMT
    next_row += 1

# ====== Sheet 3: Top Productos ======
sheet_name = "Top Productos"
if sheet_name in wb.sheetnames:
    s3 = wb[sheet_name]
else:
    s3 = wb.create_sheet(sheet_name)
    headers = ["Fecha", "Producto", "Cuenta", "Unidades", "Revenue"]
    for col, h in enumerate(headers, 1):
        c = s3.cell(row=1, column=col, value=h)
        style_header(c)
    for col, w in enumerate([12, 60, 12, 12, 14], 1):
        s3.column_dimensions[get_column_letter(col)].width = w

# Remove existing rows for this date
rows_to_delete = []
for row in range(2, s3.max_row + 1):
    if s3.cell(row=row, column=1).value == date_label:
        rows_to_delete.append(row)
for r in reversed(rows_to_delete):
    s3.delete_rows(r)

next_row = s3.max_row + 1 if s3.max_row > 1 else 2
sorted_prods = sorted(all_products.items(), key=lambda x: -x[1]["revenue"])
for (title, label), info in sorted_prods[:50]:
    s3.cell(row=next_row, column=1, value=date_label)
    s3.cell(row=next_row, column=2, value=title)
    s3.cell(row=next_row, column=3, value=label)
    s3.cell(row=next_row, column=4, value=info["qty"]).number_format = INT_FMT
    s3.cell(row=next_row, column=5, value=info["revenue"]).number_format = NUM_FMT
    next_row += 1

# ====== Sheet 4: Devoluciones ======
sheet_name = "Devoluciones"
if sheet_name in wb.sheetnames:
    s4 = wb[sheet_name]
else:
    s4 = wb.create_sheet(sheet_name)
    headers = ["Fecha", "Cuenta", "Order ID", "Producto", "Monto", "Razón"]
    for col, h in enumerate(headers, 1):
        c = s4.cell(row=1, column=col, value=h)
        style_header(c)
    for col, w in enumerate([12, 12, 18, 50, 12, 14], 1):
        s4.column_dimensions[get_column_letter(col)].width = w

rows_to_delete = []
for row in range(2, s4.max_row + 1):
    if s4.cell(row=row, column=1).value == date_label:
        rows_to_delete.append(row)
for r in reversed(rows_to_delete):
    s4.delete_rows(r)

next_row = s4.max_row + 1 if s4.max_row > 1 else 2
for ret in all_returns:
    s4.cell(row=next_row, column=1, value=ret["date"])
    s4.cell(row=next_row, column=2, value=ret["account"])
    s4.cell(row=next_row, column=3, value=str(ret["order_id"]))
    s4.cell(row=next_row, column=4, value=ret["product"])
    s4.cell(row=next_row, column=5, value=ret["amount"]).number_format = NUM_FMT
    s4.cell(row=next_row, column=6, value=ret["reason"])
    next_row += 1

# ====== Sheet 5: Charts (refresh all) ======
chart_sheet_name = "Gráficas"
if chart_sheet_name in wb.sheetnames:
    del wb[chart_sheet_name]
s5 = wb.create_sheet(chart_sheet_name)

# Chart 1: Daily revenue trend (LineChart from Resumen Diario)
last_row = s1.max_row
if last_row >= 2:
    chart1 = LineChart()
    chart1.title = "Bruto vs NET Diario"
    chart1.style = 10
    chart1.y_axis.title = "MXN"
    chart1.x_axis.title = "Fecha"
    chart1.width = 20
    chart1.height = 10
    
    # data: Bruto (col D) and NET post IVA (col K)
    data = Reference(s1, min_col=4, min_row=1, max_row=last_row, max_col=4)
    chart1.add_data(data, titles_from_data=True)
    data_net = Reference(s1, min_col=11, min_row=1, max_row=last_row, max_col=11)
    chart1.add_data(data_net, titles_from_data=True)
    cats = Reference(s1, min_col=1, min_row=2, max_row=last_row)
    chart1.set_categories(cats)
    s5.add_chart(chart1, "A1")

# Chart 2: NET por cuenta hoy (PieChart)
chart2 = PieChart()
chart2.title = f"NET por cuenta — {date_label}"
chart2.width = 15
chart2.height = 10

# Find rows for today in s2
today_rows = []
for row in range(2, s2.max_row + 1):
    if s2.cell(row=row, column=1).value == date_label:
        today_rows.append(row)
if today_rows:
    # data and labels
    cats_pie = []
    data_pie = []
    for r in today_rows:
        cats_pie.append((s2.cell(row=r, column=2).value, s2.cell(row=r, column=11).value or 0))
    if cats_pie:
        # Use a hidden range — write to s5 area
        s5.cell(row=22, column=1, value="Cuenta")
        s5.cell(row=22, column=2, value="NET")
        for i, (lbl, val) in enumerate(cats_pie):
            s5.cell(row=23+i, column=1, value=lbl)
            s5.cell(row=23+i, column=2, value=val)
        labels = Reference(s5, min_col=1, min_row=23, max_row=22+len(cats_pie))
        data_p = Reference(s5, min_col=2, min_row=22, max_row=22+len(cats_pie))
        chart2.add_data(data_p, titles_from_data=True)
        chart2.set_categories(labels)
        chart2.dataLabels = DataLabelList(showPercent=True)
        s5.add_chart(chart2, "M1")

# Chart 3: Top productos hoy (BarChart top 10)
chart3 = BarChart()
chart3.type = "bar"
chart3.title = f"Top 10 productos — {date_label}"
chart3.x_axis.title = "Revenue"
chart3.y_axis.title = "Producto"
chart3.width = 20
chart3.height = 12

today_prods_rows = [r for r in range(2, s3.max_row+1) if s3.cell(row=r, column=1).value == date_label][:10]
if today_prods_rows:
    s5.cell(row=40, column=1, value="Producto")
    s5.cell(row=40, column=2, value="Revenue")
    for i, r in enumerate(today_prods_rows):
        s5.cell(row=41+i, column=1, value=s3.cell(row=r, column=2).value)
        s5.cell(row=41+i, column=2, value=s3.cell(row=r, column=5).value)
    labels = Reference(s5, min_col=1, min_row=41, max_row=40+len(today_prods_rows))
    data_b = Reference(s5, min_col=2, min_row=40, max_row=40+len(today_prods_rows))
    chart3.add_data(data_b, titles_from_data=True)
    chart3.set_categories(labels)
    s5.add_chart(chart3, "A22")

s5.column_dimensions['A'].width = 50
s5.column_dimensions['B'].width = 14

# Move sheets in order
order = ["Resumen Diario", "Detalle por Cuenta", "Top Productos", "Devoluciones", "Gráficas"]
for i, name in enumerate(order):
    if name in wb.sheetnames:
        idx = wb.sheetnames.index(name)
        if idx != i:
            wb.move_sheet(name, offset=i-idx)

wb.save(OUTPUT)
print(f"\n✅ Saved {OUTPUT}")
print(f"\n📊 Resumen {date_label}:")
print(f"  Órdenes: {t_orders} | Unidades: {t_qty}")
print(f"  Bruto: ${t_bruto:,.0f}")
print(f"  Comisión: ${t_fees:,.0f}")
print(f"  Envío: ${t_ship:,.0f}")
print(f"  IVA: ${t_iva:,.0f}")
print(f"  Devoluciones: {t_ret_cnt} (${t_ret_amt:,.0f})")
print(f"  NET (sin IVA): ${t_net:,.0f}")
print(f"  NET (post IVA): ${t_net_after_iva:,.0f}")
