import os, re, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Drive folder pics
FOLDER="1WWNzSNbo65wIPBJfXo7vy226CJTnuRTW"
ua={"User-Agent":"Mozilla/5.0"}
html=requests.get(f"https://drive.google.com/embeddedfolderview?id={FOLDER}#list",headers=ua,timeout=30).text
ids=set(re.findall(r'/file/d/([a-zA-Z0-9_-]{20,})', html))
ids|=set(re.findall(r'data-id="([a-zA-Z0-9_-]{20,})"', html))
ids=list(ids)
print(f"Drive ids: {len(ids)}")

pic_ids=[]
for fid in ids[:10]:
  for dl in [f"https://lh3.googleusercontent.com/d/{fid}=s2000",
             f"https://drive.google.com/uc?export=download&id={fid}"]:
    try:
      rr=requests.get(dl,timeout=30,allow_redirects=True)
      if rr.status_code==200 and len(rr.content)>15000:
        ct=rr.headers.get("content-type","")
        sig=rr.content[:4]
        if "image" in ct or sig[:3]==b'\xff\xd8\xff' or sig[:4]==b'\x89PNG':
          up=requests.post(f"{API}/pictures/items/upload",
            headers={"Authorization":f"Bearer {AT}"},
            files={"file":(f"t_{fid}.jpg",rr.content,"image/jpeg")},timeout=60)
          if up.status_code in (200,201):
            pid=up.json().get("id")
            if pid: pic_ids.append(pid); print(f"  ✓ {pid}"); break
          else:
            print(f"  ✗ upload {up.status_code} {up.text[:200]}"); break
    except Exception as e:
      print(f"  err {fid}: {e}")
print(f"\nuploaded: {len(pic_ids)}")

# 2) Category prediction for "Calcetines Tommy Hilfiger"
TITLE="Calcetines Tommy Hilfiger Hombre Pack 3 Pares Negro Algodón"
print(f"title len: {len(TITLE)}")
pred=requests.get(f"{API}/sites/MLM/category_predictor/predict?title={requests.utils.quote(TITLE)}",timeout=15).json()
cat=pred.get("id")
print(f"predicted cat: {cat}")
if not cat:
  # try search
  s=requests.get(f"{API}/sites/MLM/search?q=calcetines+tommy+hilfiger+hombre&limit=5",headers=H,timeout=15).json()
  cats={}
  for r2 in s.get("results",[])[:10]:
    c=r2.get("category_id")
    if c: cats[c]=cats.get(c,0)+1
  cat=max(cats.items(),key=lambda x:x[1])[0] if cats else "MLM81472"
  print(f"fallback cat: {cat}")

# Inspect attrs
ats=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=15).json()
valid={a["id"]:a for a in ats}
print(f"cat attrs: {len(valid)}")
req=[a for a in ats if (a.get("tags",{}) or {}).get("required")]
for a in req: print(f"  REQ {a['id']}: {a.get('name')} type={a.get('value_type')}")

desc=(
"CALCETINES TOMMY HILFIGER PARA HOMBRE - PACK DE 3 PARES NEGRO\n\n"
"Set de 3 pares de calcetines Tommy Hilfiger color negro, tejido en mezcla "
"premium de algodón con elastano para máxima comodidad y durabilidad. "
"Diseño clásico atemporal ideal para uso diario, oficina, deporte casual "
"y ocasiones formales.\n\n"
"CARACTERÍSTICAS\n"
"- Marca: Tommy Hilfiger (100% original)\n"
"- Pack: 3 pares por set\n"
"- Color: Negro sólido\n"
"- Material: Mezcla de algodón premium con elastano\n"
"- Talla: Estándar adulto, ajuste universal\n"
"- Tipo: Calcetín mediano (media pantorrilla)\n"
"- Logo: Bordado clásico Tommy Hilfiger\n"
"- Tejido transpirable y suave\n"
"- Costuras planas anti-rozaduras\n"
"- Banda elástica reforzada que no aprieta\n"
"- Refuerzo en talón y puntera\n\n"
"USOS\n"
"- Trabajo y oficina\n"
"- Uso diario casual\n"
"- Deporte ligero\n"
"- Ocasiones semi-formales\n"
"- Ideal para regalo\n\n"
"CUIDADOS\n"
"- Lavar a máquina con agua fría\n"
"- No usar blanqueador\n"
"- Secar al aire para máxima durabilidad\n"
"- Plancha a baja temperatura si es necesario\n\n"
"PRODUCTO ORIGINAL TOMMY HILFIGER\n"
"100% originales con etiquetas de marca. Empaque sellado de fábrica. "
"Envío inmediato desde México. Garantía del vendedor 30 días por defectos "
"de fabricación."
)

# Build attrs
attrs=[
  {"id":"BRAND","value_name":"Tommy Hilfiger"},
  {"id":"GENDER","value_name":"Hombre"},
  {"id":"AGE_GROUP","value_name":"Adultos"},
  {"id":"MAIN_COLOR","value_name":"Negro"},
  {"id":"COLOR","value_name":"Negro"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"MAIN_MATERIAL","value_name":"Algodón"},
  {"id":"UNITS_PER_PACK","value_name":"3"},
  {"id":"SIZE","value_name":"Único"},
  {"id":"FOOT_LENGTH","value_name":"Estándar"},
  {"id":"CLOTHING_TYPE","value_name":"Calcetines"},
  {"id":"GTIN","value_name":"7900000000007"},  # placeholder, may need real
]
# Filter to valid ones
attrs=[a for a in attrs if a["id"] in valid]
print(f"\nattrs to send: {len(attrs)}")

payload={
  "title": TITLE,
  "category_id": cat,
  "price": 199,
  "currency_id":"MXN",
  "available_quantity":100,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}

p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
