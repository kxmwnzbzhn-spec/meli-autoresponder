"""Find any working SIZE_GRID_ID from existing items, try multiple chart create endpoints, then publish."""
import os, requests, json, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id"); print(f"seller={uid}")

# === STEP 1: Try multiple search variants to find seed chart ===
seed_chart_id=None
seed_chart_rows=None
queries=[
    {"q":"boxer hombre","category":"MLM194115","limit":15},
    {"q":"calvin klein boxer","limit":15},
    {"q":"boxer microfibra","limit":15},
    {"category":"MLM194115","limit":20},
]
for params in queries:
    if seed_chart_id: break
    try:
        sr=requests.get(f"{API}/sites/MLM/search",headers=H,timeout=15,params=params).json()
    except Exception as e:
        print(f"search err: {e}"); continue
    results=sr.get("results") or []
    print(f"\n[SEARCH {params}] got {len(results)} results")
    for it in results[:10]:
        iid=it.get("id")
        try:
            g=requests.get(f"{API}/items/{iid}?attributes=id,title,attributes,variations,category_id",headers=H,timeout=8).json()
        except: continue
        if g.get("category_id")!="MLM194115": continue
        sgi=next((a.get("value_id") for a in (g.get("attributes") or []) if a.get("id")=="SIZE_GRID_ID"),None)
        if sgi:
            print(f"  ✅ {iid} | {(g.get('title') or '')[:50]} | SIZE_GRID_ID={sgi}")
            seed_chart_id=sgi
            # Inspect chart
            for ce in [f"/catalog_charts/{sgi}", f"/charts/{sgi}"]:
                cc=requests.get(f"{API}{ce}",headers=H,timeout=10)
                print(f"  GET {ce}: HTTP {cc.status_code}: {cc.text[:600]}")
                if cc.status_code==200:
                    cd=cc.json()
                    seed_chart_rows=cd.get("rows") or cd.get("attributes")
                    print(f"  rows preview:")
                    for rr in (cd.get("rows") or [])[:6]:
                        ats={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr.get('attributes') or [])}
                        print(f"    row_id={rr.get('id')} {ats}")
                    break
            break
    if seed_chart_id: break

# === STEP 2: Try multiple chart-create endpoints ===
print("\n=== Try chart-create endpoints ===")
chart_payload={
    "names": {"main_title": "Calvin Klein Boxers Hombre"},
    "domain_id": "MLM-UNDERPANTS",
    "site_id": "MLM",
    "type": "specific",
    "attributes": [
        {"id": "BRAND", "values": [{"name": "Calvin Klein"}]},
        {"id": "GENDER", "values": [{"name": "Hombre"}]}
    ],
    "rows": [
        {"attributes": [{"id":"SIZE","values":[{"name":"S"}]}, {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"71-76 cm"}]}]},
        {"attributes": [{"id":"SIZE","values":[{"name":"M"}]}, {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"81-86 cm"}]}]},
        {"attributes": [{"id":"SIZE","values":[{"name":"L"}]}, {"id":"WAIST_CIRCUMFERENCE","values":[{"name":"91-97 cm"}]}]}
    ]
}
created_chart_id=None
for ep in [
    "/catalog_charts",
    "/charts",
    f"/users/{uid}/charts",
    f"/catalog_charts/users/{uid}/charts",
    "/sites/MLM/charts",
]:
    cr=requests.post(f"{API}{ep}",headers=HJ,json=chart_payload,timeout=20)
    print(f"  POST {ep} → HTTP {cr.status_code}: {cr.text[:400]}")
    if cr.status_code in (200,201):
        created_chart_id=(cr.json().get("id") or cr.json().get("chart_id"))
        print(f"  ✅ CHART CREATED at {ep} → id={created_chart_id}")
        break

chart_id = created_chart_id or seed_chart_id
if not chart_id:
    print("\n[FAIL] no chart endpoint funcionó y no encontré chart de seed")
    print("Hay que crear el chart desde la UI de MELI manualmente.")
    raise SystemExit(0)

print(f"\n=== USING chart_id={chart_id} ===")

# === STEP 3: Try to publish with the chart_id ===
PICS=[
  "https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_958202-MLA106740502843_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_890097-MLA106741215883_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_909047-MLA106740740811_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_639680-MLA106741215897_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_977787-MLA106740622519_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_964357-MLA106119905012_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_886035-MLA106120083064_022026-F.jpg",
]
DESC=("Pack de 3 boxers Calvin Klein de microfibra premium, importados de USA. "
      "Diseñados para máxima comodidad y ajuste perfecto durante todo el día.\n\n"
      "🔹 Características: Microfibra sedosa, elástico con logo CK, colores mixtos (negro, gris oxford, gris cemento).\n"
      "🔹 Guía de tallas:\n"
      "• S — Cintura 71-76 cm | Cadera 86-91 cm\n"
      "• M — Cintura 81-86 cm | Cadera 94-99 cm\n"
      "• L — Cintura 91-97 cm | Cadera 102-107 cm\n"
      "🔹 Importados de USA — 100% original.\n"
      "🔹 Envío inmediato. Garantía 30 días.")

published=[]
SIZES=[("S","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla S"),
       ("M","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla M"),
       ("L","Calvin Klein Pack 3 Boxers Microfibra Hombre Talla L")]

# Try to find row_id per size from seed chart
size_to_row={}
if seed_chart_rows and isinstance(seed_chart_rows,list):
    for rr in seed_chart_rows:
        ats={a.get('id'):(a.get('values') or [{}])[0].get('name') for a in (rr.get('attributes') or [])}
        size_val=ats.get("SIZE","").strip().upper()
        if size_val in ("S","M","L","CHICA","MEDIANA","GRANDE","CH","M","G"):
            size_to_row[size_val[0] if size_val[0] in "SML" else size_val]=rr.get("id")
print(f"\nsize→row mapping: {size_to_row}")

for size,title in SIZES:
    print(f"\n========== TALLA {size} ==========")
    attrs=[
        {"id":"BRAND","value_name":"Calvin Klein"},
        {"id":"MODEL","value_name":"Brief"},
        {"id":"GENDER","value_name":"Hombre"},
        {"id":"COLOR","value_name":"Mixto"},
        {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
        {"id":"SIZE","value_name":size},
        {"id":"SIZE_GRID_ID","value_id":chart_id},
    ]
    if size in size_to_row:
        attrs.append({"id":"SIZE_GRID_ROW_ID","value_id":size_to_row[size]})
    payload={
        "title":title,
        "category_id":"MLM194115",
        "price":799,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "condition":"new",
        "listing_type_id":"gold_special",
        "pictures":[{"source":u} for u in PICS],
        "attributes":attrs,
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"},
        ],
    }
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=20)
    print(f"  validate HTTP {rv.status_code}: {rv.text[:600]}")
    if rv.status_code not in (200,204):
        continue
    rp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"  POST HTTP {rp.status_code}: {rp.text[:400]}")
    if rp.status_code in (200,201):
        it=rp.json(); iid=it.get("id"); link=it.get("permalink")
        print(f"  ✅ {iid} | {link}")
        requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":DESC},timeout=15)
        published.append({"size":size,"item_id":iid,"link":link})
    time.sleep(1)

print(f"\n=== FINAL ===")
for p in published: print(f"  {p['size']}: {p['item_id']} → {p['link']}")
print(f"TOTAL: {len(published)}/3")
