"""
Etiquetas de envíos PENDIENTES DE ENTREGAR (ya impresas/listas en MELI),
excluyendo las que aún están "pending" (no se ha generado etiqueta).
Filtra por shipping.status in ("ready_to_ship","handling","shipped").
"""
import os, requests, json, sys, re
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

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
]

# Estados de shipping que QUEREMOS (ya impresas, falta entregar):
INCLUDE_STATUSES = {"ready_to_ship"}  # SOLO con etiqueta lista, no entregadas, no pending
# Excluir: "pending" (sin etiqueta), "shipped" (ya en tránsito), "delivered" (ya entregado)

def categorize(title):
    t = (title or "").lower()
    color = "S/Color"
    for c in ["azul","rojo","roja","negro","negra","blanco","blanca","rosa","camuflaje","camo","aqua","celeste","morado","morada","violeta","verde","amarillo"]:
        if c in t: color = c.capitalize(); break
    if "go 4" in t or "go4" in t: return ("JBL Go 4", color)
    if "go 3" in t or "go3" in t: return ("JBL Go 3", color)
    if "go essential" in t: return ("JBL Go Essential", color)
    if "flip 7" in t or "flip7" in t: return ("JBL Flip 7", color)
    if "flip 6" in t: return ("JBL Flip 6", color)
    if "charge 6" in t: return ("JBL Charge 6", color)
    if "charge 5" in t: return ("JBL Charge 5", color)
    if "grip" in t and "jbl" in t: return ("JBL Grip", color)
    if "clip 5" in t: return ("JBL Clip 5", color)
    if "xb100" in t: return ("Sony XB100", color)
    if "armaf" in t and "club de nuit" in t: return ("Armaf Club De Nuit", color)
    if "armaf" in t and "odyssey" in t: return ("Armaf Odyssey", color)
    if "armaf" in t and "delight" in t: return ("Armaf Delight", color)
    if "armaf" in t: return ("Armaf otros", color)
    if "lattafa" in t: return ("Lattafa", color)
    if "angel" in t: return ("Angel/Mugler", color)
    if "perfume" in t or "edp" in t or "edt" in t: return ("Perfume otro", color)
    if "buds" in t: return ("Auriculares", color)
    return ("Otros", color)

now_cdmx = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d_%H%M")
OUTDIR = f"labels_pending_{now_cdmx}"
os.makedirs(OUTDIR, exist_ok=True)
print(f"📅 Corte etiquetas pendientes de entregar: {now_cdmx}\n")

# Pull shipments (últimos 14 días para no perder ninguno antiguo aún en handling)
cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
yesterday_cdmx = (cdmx - timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
date_from = yesterday_cdmx.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
rng = yesterday_cdmx.strftime("%Y-%m-%d"); print(f"Rango: {rng} CDMX → hoy")

groups = defaultdict(list)
total_shipments = 0; total_units = 0
errors = []
status_counts = defaultdict(int)

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
            data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
            timeout=15).json()
        H = {"Authorization":f"Bearer {r['access_token']}"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"[{label}] auth err: {e}"); continue
    
    print(f"[{label}] {me.get('nickname','')}")
    offset = 0; account_count = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
        results = rr.get("results",[])
        if not results: break
        for o in results:
            if o.get("status") not in ("paid","shipped"): continue
            sh = o.get("shipping",{}) or {}
            sh_id = sh.get("id")
            if not sh_id: continue
            
            # GET shipment to check shipping.status
            try:
                sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
                ship_status = sd.get("status","")
                substatus = sd.get("substatus","")
            except:
                continue
            status_counts[f"{ship_status}/{substatus or '-'}"] += 1
            
            if ship_status not in INCLUDE_STATUSES: continue
            
            buyer = (o.get("buyer") or {}).get("nickname","")
            for oi in o.get("order_items",[]):
                title = (oi.get("item") or {}).get("title","")
                qty = oi.get("quantity",0)
                model, color = categorize(title)
                groups[f"{model}|{color}"].append({
                    "account": label,
                    "shipment_id": sh_id,
                    "order_id": o.get("id"),
                    "qty": qty,
                    "title": title[:60],
                    "buyer": buyer,
                    "ship_status": ship_status,
                    "_token": H["Authorization"],
                })
                account_count += 1
                total_shipments += 1
                total_units += qty
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    print(f"  → {account_count} envíos pendientes de entregar")

print(f"\n=== Conteo por status (incluye descartados) ===")
for s, c in sorted(status_counts.items(), key=lambda x: -x[1])[:15]:
    mark = "✓" if s.split("/")[0] in INCLUDE_STATUSES else "✗"
    print(f"  {mark} {s}: {c}")

print(f"\n📦 INCLUIDOS: {total_shipments} envíos / {total_units} unidades / {len(groups)} grupos\n")

# Download labels
labels_index = []
for key, items in sorted(groups.items()):
    if not items: continue
    model, color = key.split("|", 1)
    safe_key = re.sub(r'[^A-Za-z0-9]+','_', f"{model}_{color}").strip("_")
    
    by_account = defaultdict(list)
    for it in items: by_account[it["account"]].append(it)
    
    print(f"📦 {model} - {color} ({len(items)} envíos)")
    
    all_pdf_bytes = []
    for acct, acct_items in by_account.items():
        sh_ids = ",".join(str(i["shipment_id"]) for i in acct_items)
        token = acct_items[0]["_token"]
        try:
            r = requests.get(f"https://api.mercadolibre.com/shipment_labels?shipment_ids={sh_ids}&response_type=pdf",
                headers={"Authorization": token}, timeout=60)
            if r.status_code == 200 and r.headers.get("content-type","").startswith("application/pdf"):
                all_pdf_bytes.append(r.content)
                print(f"  ✓ {acct}: {len(acct_items)} envíos → {len(r.content)//1024} KB")
            else:
                print(f"  ❌ {acct}: HTTP {r.status_code} {r.text[:120]}")
                errors.append({"account":acct,"key":key,"err":r.text[:200]})
        except Exception as e:
            print(f"  ❌ {acct}: {e}"); errors.append({"account":acct,"err":str(e)})
    
    if all_pdf_bytes:
        out_pdf = f"{OUTDIR}/{safe_key}.pdf"
        try:
            from pypdf import PdfWriter, PdfReader
            from io import BytesIO
            writer = PdfWriter()
            for pdf_bytes in all_pdf_bytes:
                try:
                    reader = PdfReader(BytesIO(pdf_bytes))
                    for p in reader.pages: writer.add_page(p)
                except Exception as e:
                    print(f"  pdf concat err: {e}")
            with open(out_pdf, "wb") as f: writer.write(f)
        except Exception as e:
            print(f"  fallback save first PDF only: {e}")
            try:
                with open(out_pdf, "wb") as f: f.write(all_pdf_bytes[0])
            except: pass
        labels_index.append({
            "key": key, "model": model, "color": color,
            "envios": len(items), "unidades": sum(i["qty"] for i in items),
            "file": f"{safe_key}.pdf", "items": items,
        })

# Manifest XLSX
wb = Workbook(); wb.remove(wb.active)
ws = wb.create_sheet("Resumen")
ws["A1"] = f"📋 Pendientes de entregar — {now_cdmx}"
ws["A1"].font = Font(bold=True, size=16, color="1F4E78"); ws.merge_cells("A1:F1")
HEADER = ["Modelo","Color","Envíos","Unidades","Archivo","Cuentas"]
for i, h in enumerate(HEADER, 1):
    c = ws.cell(row=3, column=i, value=h)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="1F4E78")
r = 4
for grp in sorted(labels_index, key=lambda x: -x["envios"]):
    cuentas = sorted({i["account"] for i in grp["items"]})
    ws.cell(row=r, column=1, value=grp["model"])
    ws.cell(row=r, column=2, value=grp["color"])
    ws.cell(row=r, column=3, value=grp["envios"])
    ws.cell(row=r, column=4, value=grp["unidades"])
    ws.cell(row=r, column=5, value=grp["file"])
    ws.cell(row=r, column=6, value=", ".join(cuentas))
    r += 1

ws2 = wb.create_sheet("Detalle")
HEADER2 = ["Modelo","Color","Cuenta","Order ID","Shipment","Cant","Comprador","Status","Título"]
for i, h in enumerate(HEADER2, 1):
    c = ws2.cell(row=1, column=i, value=h)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="1F4E78")
r = 2
for grp in labels_index:
    for it in grp["items"]:
        ws2.cell(row=r, column=1, value=grp["model"])
        ws2.cell(row=r, column=2, value=grp["color"])
        ws2.cell(row=r, column=3, value=it["account"])
        ws2.cell(row=r, column=4, value=str(it["order_id"]))
        ws2.cell(row=r, column=5, value=str(it["shipment_id"]))
        ws2.cell(row=r, column=6, value=it["qty"])
        ws2.cell(row=r, column=7, value=it["buyer"])
        ws2.cell(row=r, column=8, value=it["ship_status"])
        ws2.cell(row=r, column=9, value=it["title"])
        r += 1
for ws_x in [ws, ws2]:
    for col in ws_x.columns:
        max_len = max((len(str(c.value)) if c.value else 0 for c in col), default=10)
        ws_x.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
wb.save(f"{OUTDIR}/manifest.xlsx")

print(f"\n✅ {len(labels_index)} grupos en {OUTDIR}/")

if TG_TOKEN and TG_CHAT and total_shipments > 0:
    text = f"📦 *Etiquetas pendientes de entregar — {now_cdmx}*\n{total_shipments} envíos / {total_units} unid / {len(labels_index)} grupos\n\nTop:\n"
    for grp in sorted(labels_index, key=lambda x: -x["envios"])[:8]:
        text += f"• {grp['model']} {grp['color']}: {grp['envios']}\n"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id":TG_CHAT,"text":text,"parse_mode":"Markdown"})
