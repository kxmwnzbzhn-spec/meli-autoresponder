"""
Etiquetas pendientes de entregar (SOLO ready_to_ship), agrupadas por COMPOSICIÓN.
Cada shipment es la unidad — si trae múltiples items se etiqueta como MIXTO con
la composición exacta (ej. "MIXTO Go4_Azul_x1+Go4_Rojo_x1").
"""
import os, requests, re
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

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

INCLUDE_STATUSES = {"ready_to_ship"}
EXCLUDE_SUBSTATUS = {"picked_up"}  # printed + ready_to_print (excluye solo recolectado)

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
    if "armaf" in t: return ("Armaf", color)
    if "lattafa" in t: return ("Lattafa", color)
    if "angel" in t: return ("Angel/Mugler", color)
    if "perfume" in t or "edp" in t or "edt" in t: return ("Perfume", color)
    if "buds" in t: return ("Auriculares", color)
    return ("Otros", color)

cdmx = datetime.now(timezone.utc) - timedelta(hours=6)
window_start = (cdmx - timedelta(days=3)).replace(hour=0,minute=0,second=0,microsecond=0)
date_from = window_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
print(f"📅 Rango: {window_start.strftime('%Y-%m-%d')} CDMX → ahora")

now_cdmx = cdmx.strftime("%Y-%m-%d_%H%M")
OUTDIR = f"labels_pending_{now_cdmx}"
os.makedirs(OUTDIR, exist_ok=True)

# shipments_data[(account, shipment_id)] = {composition_key, items, ...}
shipments = {}
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
            try:
                sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
                ship_status = sd.get("status","")
                substatus = sd.get("substatus","")
            except: continue
            status_counts[f"{ship_status}/{substatus or '-'}"] += 1
            if ship_status not in INCLUDE_STATUSES: continue
            if substatus in EXCLUDE_SUBSTATUS: continue
            
            # Compose items per shipment
            buyer = (o.get("buyer") or {}).get("nickname","")
            items_in_order = []
            for oi in o.get("order_items",[]):
                title = (oi.get("item") or {}).get("title","")
                qty = oi.get("quantity",0)
                model, color = categorize(title)
                items_in_order.append({"model":model,"color":color,"qty":qty,"title":title[:60]})
            
            key = (label, sh_id)
            if key in shipments:
                shipments[key]["items"].extend(items_in_order)
                shipments[key]["orders"].append(o.get("id"))
            else:
                shipments[key] = {
                    "account": label,
                    "shipment_id": sh_id,
                    "orders": [o.get("id")],
                    "items": items_in_order,
                    "buyer": buyer,
                    "ship_status": ship_status,
                    "_token": H["Authorization"],
                }
            account_count += 1
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    print(f"  → {account_count} envíos pendientes")

print(f"\n=== Status (incluye descartados) ===")
for s, c in sorted(status_counts.items(), key=lambda x: -x[1])[:10]:
    mark = "✓" if s.split("/")[0] in INCLUDE_STATUSES else "✗"
    print(f"  {mark} {s}: {c}")

# Compute composition per shipment + group
def composition_signature(items):
    """ej: 'JBL_Go_4_Azul_x1+JBL_Go_4_Rojo_x1' (sorted)"""
    consol = defaultdict(int)
    for it in items:
        k = f"{it['model']}_{it['color']}"
        k = re.sub(r'[^A-Za-z0-9_]+','_', k).strip("_")
        consol[k] += it["qty"]
    parts = sorted(f"{k}_x{v}" for k,v in consol.items())
    return "+".join(parts)

groups = defaultdict(list)
mixed_shipments = []
for sh in shipments.values():
    sig = composition_signature(sh["items"])
    sh["composition"] = sig
    is_mixed = len({(it["model"],it["color"]) for it in sh["items"]}) > 1
    if is_mixed:
        sh["composition"] = "MIXTO__" + sig
        mixed_shipments.append(sh)
    groups[sh["composition"]].append(sh)

total_shipments = len(shipments)
total_units = sum(sum(i["qty"] for i in s["items"]) for s in shipments.values())
print(f"\n📦 INCLUIDOS: {total_shipments} envíos / {total_units} unidades / {len(groups)} grupos ({len(mixed_shipments)} MIXTOS)\n")

# Download labels per group
labels_index = []
for sig, ships in sorted(groups.items()):
    if not ships: continue
    safe_key = re.sub(r'[^A-Za-z0-9_+]+','_', sig).strip("_")[:80]
    is_mixed = sig.startswith("MIXTO__")
    
    by_account = defaultdict(list)
    for s in ships: by_account[s["account"]].append(s)
    
    icon = "⚠️ MIXTO" if is_mixed else "📦"
    print(f"{icon} {sig} ({len(ships)} envíos)")
    
    all_pdf_bytes = []
    for acct, acct_ships in by_account.items():
        sh_ids = ",".join(str(s["shipment_id"]) for s in acct_ships)
        token = acct_ships[0]["_token"]
        try:
            r = requests.get(f"https://api.mercadolibre.com/shipment_labels?shipment_ids={sh_ids}&response_type=pdf",
                headers={"Authorization": token}, timeout=60)
            if r.status_code == 200 and r.headers.get("content-type","").startswith("application/pdf"):
                all_pdf_bytes.append(r.content)
                print(f"  ✓ {acct}: {len(acct_ships)} envíos → {len(r.content)//1024} KB")
            else:
                print(f"  ❌ {acct}: HTTP {r.status_code} {r.text[:120]}")
        except Exception as e:
            print(f"  ❌ {acct}: {e}")
    
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
            print(f"  fallback: {e}")
            try:
                with open(out_pdf, "wb") as f: f.write(all_pdf_bytes[0])
            except: pass
        labels_index.append({
            "sig": sig, "file": f"{safe_key}.pdf", "is_mixed": is_mixed,
            "envios": len(ships), "unidades": sum(sum(i["qty"] for i in s["items"]) for s in ships),
            "ships": ships,
        })

# Manifest XLSX
wb = Workbook(); wb.remove(wb.active)
ws = wb.create_sheet("Resumen")
ws["A1"] = f"📋 Pendientes de entregar — {now_cdmx}"
ws["A1"].font = Font(bold=True, size=16, color="1F4E78"); ws.merge_cells("A1:F1")
HEADER = ["Composición","Envíos","Unidades","Tipo","Archivo","Cuentas"]
for i, h in enumerate(HEADER, 1):
    c = ws.cell(row=3, column=i, value=h)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="1F4E78")
RED = PatternFill("solid", fgColor="FFC7CE")
r = 4
for grp in sorted(labels_index, key=lambda x: -x["envios"]):
    cuentas = sorted({s["account"] for s in grp["ships"]})
    pretty = grp["sig"].replace("MIXTO__","").replace("_x"," x").replace("+"," + ").replace("_"," ")
    ws.cell(row=r, column=1, value=pretty)
    ws.cell(row=r, column=2, value=grp["envios"])
    ws.cell(row=r, column=3, value=grp["unidades"])
    tcell = ws.cell(row=r, column=4, value="MIXTO" if grp["is_mixed"] else "Solo")
    if grp["is_mixed"]: tcell.fill = RED
    ws.cell(row=r, column=5, value=grp["file"])
    ws.cell(row=r, column=6, value=", ".join(cuentas))
    r += 1

ws2 = wb.create_sheet("Detalle envíos")
HEADER2 = ["Cuenta","Order ID","Shipment","Composición","# items","Comprador","Status","Detalle items"]
for i, h in enumerate(HEADER2, 1):
    c = ws2.cell(row=1, column=i, value=h)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="1F4E78")
r = 2
for grp in labels_index:
    for s in grp["ships"]:
        items_str = "; ".join(f"{i['model']} {i['color']} x{i['qty']}" for i in s["items"])
        is_mixed = len({(i["model"],i["color"]) for i in s["items"]}) > 1
        ws2.cell(row=r, column=1, value=s["account"])
        ws2.cell(row=r, column=2, value=", ".join(str(o) for o in s["orders"]))
        ws2.cell(row=r, column=3, value=str(s["shipment_id"]))
        ws2.cell(row=r, column=4, value=grp["sig"].replace("MIXTO__",""))
        ws2.cell(row=r, column=5, value=len(s["items"]))
        ws2.cell(row=r, column=6, value=s["buyer"])
        ws2.cell(row=r, column=7, value=s["ship_status"])
        cell_d = ws2.cell(row=r, column=8, value=items_str)
        if is_mixed:
            for c_idx in range(1, 9): ws2.cell(row=r, column=c_idx).fill = RED
        r += 1

for ws_x in [ws, ws2]:
    for ci in range(1, ws_x.max_column+1):
        max_len = 10
        for ri in range(1, ws_x.max_row+1):
            try:
                v = ws_x.cell(row=ri, column=ci).value
                if v: max_len = max(max_len, len(str(v)))
            except: pass
        ws_x.column_dimensions[get_column_letter(ci)].width = min(max_len + 2, 80)

wb.save(f"{OUTDIR}/manifest.xlsx")

print(f"\n✅ {len(labels_index)} grupos en {OUTDIR}/")
if mixed_shipments:
    print(f"⚠️  {len(mixed_shipments)} envíos MIXTOS — revisar manifest.xlsx para empaque correcto")

if TG_TOKEN and TG_CHAT and total_shipments > 0:
    text = f"📦 *Etiquetas — {now_cdmx}*\n{total_shipments} envíos / {total_units} unid / {len(labels_index)} grupos"
    if mixed_shipments:
        text += f"\n⚠️ {len(mixed_shipments)} envíos MIXTOS"
    text += "\n\nTop:\n"
    for grp in sorted(labels_index, key=lambda x: -x["envios"])[:8]:
        pretty = grp["sig"].replace("MIXTO__","⚠️ MIXTO ").replace("_x"," x").replace("+"," + ").replace("_"," ")
        text += f"• {pretty}: {grp['envios']}\n"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id":TG_CHAT,"text":text,"parse_mode":"Markdown"})
