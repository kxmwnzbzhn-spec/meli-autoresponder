"""Backfill listings: por cada cuenta activa, jala todos los items y los inserta en listings table."""
import os,re,requests,psycopg2
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
DSN=os.environ["SUPABASE_DB_URL"]

def tok(rt):
    if not rt: return None
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
    return r.get("access_token")

MODEL_RX=[
  (r"flip\s*7","FLIP7"),(r"clip\s*7","CLIP7"),(r"charge\s*6","CHARGE6"),
  (r"clip\s*5","CLIP5"),(r"clip\s*4","CLIP4"),(r"go\s*4","GO4"),(r"go\s*3","GO3"),
  (r"grip","GRIP"),(r"xb[\s\-]*100","XB100"),(r"bose|soundlink","BOSE"),
  (r"redmi buds","REDMI-BUDS-4-LITE"),(r"dashcam","DASHCAM-ASV-DC170"),
]
COLOR_RX=[(r"camuflaj|camo|squad|verde musg","CAMUFLAJE"),(r"aqua|celeste","AQUA"),
  (r"azul marino|azul oscuro","AZUL-MARINO"),(r"morad|violet|purpur","MORADO"),
  (r"rosa|pink","ROSA"),(r"roj","ROJO"),(r"blanc","BLANCO"),(r"azul","AZUL"),(r"negr","NEGRO")]

def classify(title):
    t=(title or "").lower()
    m=None
    for rx,mn in MODEL_RX:
        if re.search(rx,t): m=mn; break
    if not m: return None
    if m in ("XB100",): return f"SONY-{m}-NEGRO"
    if m=="DASHCAM-ASV-DC170": return f"{m}-X"
    if m=="REDMI-BUDS-4-LITE": return f"REDMI-BUDS-4-LITE-NEGRO"
    c=None
    for rx,cn in COLOR_RX:
        if re.search(rx,t): c=cn; break
    if m=="GO4" and c=="AZUL": c="AZUL-MARINO"
    return f"JBL-{m}-{c or 'XX'}" if m not in ("BOSE",) else f"BOSE-{c or 'NEGRO'}"

conn=psycopg2.connect(DSN); cur=conn.cursor()
cur.execute("SELECT id, nickname, refresh_token_secret FROM accounts WHERE active=true")
accts=cur.fetchall()
inserted=0; unmapped=set()
for aid,nick,secret_name in accts:
    T=tok(os.environ.get(secret_name,""))
    if not T:
        print(f"  {nick}: NO_TOKEN"); continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me.get("id")
    if not uid: continue
    ids=[]
    for st in ("active","paused"):
        off=0
        while True:
            r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=15).json()
            res=r.get("results",[])
            if not res: break
            ids+=res; off+=100
            if off>=r.get("paging",{}).get("total",0): break
    print(f"  {nick}: {len(ids)} items")
    for i in range(0,len(ids),20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,catalog_product_id,price,status,sub_status,available_quantity,sold_quantity",headers=H).json()
        for x in r:
            b=x.get("body",{}) or {}
            mlm=b.get("id")
            if not mlm: continue
            sku=classify(b.get("title",""))
            if not sku:
                unmapped.add(mlm); continue
            # Ensure product exists (create stub if needed)
            cur.execute("""INSERT INTO products (sku, modelo, color, brand, line, condition)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (sku) DO NOTHING""",
                (sku, sku.split('-')[1] if '-' in sku else None, sku.split('-')[-1] if '-' in sku else None, sku.split('-')[0] if '-' in sku else None, 'Bocina', b.get("condition") or "new"))
            cur.execute("""INSERT INTO listings (mlm_id, account_id, sku, title, catalog_product_id, price, status, sub_status, available_quantity, sold_quantity, last_sync)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (mlm_id) DO UPDATE SET account_id=EXCLUDED.account_id, sku=EXCLUDED.sku, title=EXCLUDED.title,
                  catalog_product_id=EXCLUDED.catalog_product_id, price=EXCLUDED.price, status=EXCLUDED.status,
                  sub_status=EXCLUDED.sub_status, available_quantity=EXCLUDED.available_quantity,
                  sold_quantity=EXCLUDED.sold_quantity, last_sync=NOW()""",
                (mlm, aid, sku, b.get("title"), b.get("catalog_product_id"), b.get("price"), b.get("status"), ','.join(b.get("sub_status") or []), b.get("available_quantity"), b.get("sold_quantity")))
            inserted+=1
conn.commit()
print(f"✓ backfill done: {inserted} listings, {len(unmapped)} unmapped: {list(unmapped)[:10]}")
cur.close(); conn.close()
