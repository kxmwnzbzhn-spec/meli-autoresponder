"""Identifica las publicaciones JBL Go 4 y Go 3 mas vendidas en todas las cuentas."""
import os, requests, time
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

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

def detect(t):
    t=(t or "").lower()
    if "go 4" in t or "go4" in t: return "Go 4"
    if "go 3" in t or "go3" in t: return "Go 3"
    return None

def detect_color(t):
    t=(t or "").lower()
    colors = [("camuflaj","Camuflaje"),("camo","Camuflaje"),("azul marino","Azul Marino"),
              ("aqua","Aqua"),("celeste","Aqua"),("negr","Negro"),("black","Negro"),
              ("roj","Rojo"),(" red","Rojo"),("rosa","Rosa"),("pink","Rosa"),
              ("morad","Morado"),("violeta","Morado"),("purple","Morado"),("purpura","Morado"),
              (" azul","Azul"),(" blue","Azul")]
    for k,v in colors:
        if k in (" "+t):
            return v
    return "?"

go4 = []
go3 = []

for acc, rt in ACCS.items():
    if not rt: continue
    print(f"\n=== {acc} ===")
    at = tok(rt)
    if not at: continue
    H={"Authorization":f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid = me.get("id")
    if not uid: continue

    # Listar items en TODOS los estados
    all_iids = []
    for st in ["active","paused"]:
        offset=0
        while True:
            rr=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
            b=rr.get("results",[])
            if not b: break
            all_iids.extend(b)
            offset += 50
            if offset >= rr.get("paging",{}).get("total",0): break

    print(f"  total items: {len(all_iids)}")

    # Bulk fetch
    for i in range(0, len(all_iids), 20):
        chunk = all_iids[i:i+20]
        rr = requests.get("https://api.mercadolibre.com/items",headers=H,
                         params={"ids":",".join(chunk),
                          "attributes":"id,title,price,status,sold_quantity,catalog_listing,catalog_product_id"},
                         timeout=20).json()
        for resp in rr:
            if resp.get("code") != 200: continue
            it = resp.get("body")
            title = it.get("title","")
            model = detect(title)
            if not model: continue
            sold = int(it.get("sold_quantity") or 0)
            color = detect_color(title)
            entry = {
                "iid": it["id"],
                "account": acc,
                "title": title[:70],
                "color": color,
                "sold": sold,
                "price": it.get("price"),
                "status": it.get("status"),
                "catalog": bool(it.get("catalog_listing")),
                "cpid": it.get("catalog_product_id"),
            }
            if model == "Go 4": go4.append(entry)
            else: go3.append(entry)
        time.sleep(0.15)

# Ordenar por sold desc
go4.sort(key=lambda x: -x["sold"])
go3.sort(key=lambda x: -x["sold"])

# Top por modelo
print(f"\n{'='*70}\n=== TOP JBL Go 4 (top 25) ===")
print(f"{'cuenta':<10} {'sold':>5} {'$':>5} {'st':<8} {'color':<14} {'iid':<14} title")
total_go4_sold = 0
for e in go4[:25]:
    print(f"{e['account']:<10} {e['sold']:>5} {str(e['price'] or ''):>5} {e['status']:<8} {e['color']:<14} {e['iid']:<14} {e['title']}")
    total_go4_sold += e['sold']
print(f"\nTotal Go4 ventas top 25: {total_go4_sold}")
print(f"Total Go4 publicaciones: {len(go4)}")
print(f"SUMA Go4 ventas TODAS: {sum(e['sold'] for e in go4)}")

print(f"\n=== TOP JBL Go 3 ===")
print(f"{'cuenta':<10} {'sold':>5} {'$':>5} {'st':<8} {'color':<14} {'iid':<14} title")
for e in go3[:15]:
    print(f"{e['account']:<10} {e['sold']:>5} {str(e['price'] or ''):>5} {e['status']:<8} {e['color']:<14} {e['iid']:<14} {e['title']}")
print(f"\nTotal Go3 publicaciones: {len(go3)}")
print(f"SUMA Go3 ventas TODAS: {sum(e['sold'] for e in go3)}")

# CSV
import csv
with open("top_jbl_go4_go3.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["model","account","sold","price","status","color","iid","cpid","catalog","title"])
    for e in go4: w.writerow(["Go 4",e["account"],e["sold"],e["price"],e["status"],e["color"],e["iid"],e["cpid"],e["catalog"],e["title"]])
    for e in go3: w.writerow(["Go 3",e["account"],e["sold"],e["price"],e["status"],e["color"],e["iid"],e["cpid"],e["catalog"],e["title"]])
print("\nCSV: top_jbl_go4_go3.csv")

# TG
if TG and TGCID:
    msg = "🏆 *Top JBL Go 4 + Go 3 vendidas*\n\n"
    msg += "*Go 4 — Top 10:*\n"
    for e in go4[:10]:
        msg += f"`{e['iid']}` {e['account']} *{e['sold']}* sold ${e['price']} {e['color']}\n"
    msg += f"\nTotal Go4 ventas: *{sum(e['sold'] for e in go4):,}* en {len(go4)} pubs\n"
    msg += "\n*Go 3 — Top 10:*\n"
    for e in go3[:10]:
        msg += f"`{e['iid']}` {e['account']} *{e['sold']}* sold ${e['price']} {e['color']}\n"
    msg += f"\nTotal Go3 ventas: *{sum(e['sold'] for e in go3):,}* en {len(go3)} pubs"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={
        "chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]},timeout=20)
