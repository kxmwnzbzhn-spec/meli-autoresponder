import os, re, json, time, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Scrape Drive folder for file IDs
FOLDER="1B_qN2PY5Xm2xjSswGLSajVcCVXTT6OuZ"
url=f"https://drive.google.com/embeddedfolderview?id={FOLDER}#list"
ua={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
html=requests.get(url,headers=ua,timeout=30).text
# Extract file IDs: pattern is data-id="XYZ" or href="/file/d/XYZ"
ids=set(re.findall(r'/file/d/([a-zA-Z0-9_-]{20,})', html))
ids|=set(re.findall(r'data-id="([a-zA-Z0-9_-]{20,})"', html))
ids=list(ids)
print(f"Drive file ids: {len(ids)}")
for i in ids: print(f"  {i}")

# 2) Download each + upload to MELI
pic_ids=[]
for fid in ids[:10]:
    for dl_url in [f"https://lh3.googleusercontent.com/d/{fid}=s2000",
                   f"https://drive.google.com/uc?export=download&id={fid}"]:
        try:
            rr=requests.get(dl_url,timeout=30,allow_redirects=True)
            if rr.status_code==200 and len(rr.content)>5000:
                ct=rr.headers.get("content-type","")
                if "image" in ct or rr.content[:3]==b'\xff\xd8\xff' or rr.content[:4]==b'\x89PNG':
                    fn=f"/tmp/{fid}.jpg"
                    open(fn,"wb").write(rr.content)
                    up=requests.post(f"{API}/pictures/items/upload",
                        headers={"Authorization":f"Bearer {AT}"},
                        files={"file":(f"{fid}.jpg",rr.content,"image/jpeg")},timeout=60)
                    if up.status_code in (200,201):
                        d=up.json()
                        pid=d.get("id")
                        if pid:
                            pic_ids.append(pid)
                            print(f"  ✓ uploaded {fid}: id={pid}")
                            break
                    else:
                        print(f"  ✗ upload {fid}: {up.status_code} {up.text[:200]}")
                        break
        except Exception as e:
            print(f"  err {fid}: {e}")
            continue

print(f"\ntotal pics uploaded to MELI: {len(pic_ids)}")
if len(pic_ids)<1:
    print("FATAL no pics"); raise SystemExit(1)

# 3) Category prediction
TITLE="Perfume Bharara Viking Beirut Parfum 100ml Hombre Mujer"
pred=requests.get(f"{API}/sites/MLM/category_predictor/predict?title={requests.utils.quote(TITLE)}",timeout=15)
cat=pred.json().get("id") if pred.status_code==200 else None
print(f"predicted category: {cat}")
if not cat:
    cat="MLM173083"  # perfumería hombre fallback

# 4) Build payload
PRICE=1500
desc=(
"Bharara Viking Beirut — Parfum Unisex 100ml.\n\n"
"Bharara Beauty lanzó Viking Beirut en 2024: una fragancia aromática fresca y "
"sofisticada inspirada en el Mediterráneo. Capa olfativa balanceada para hombre y mujer, "
"con larga duración propia de un Parfum (concentración superior a EDP).\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Salida: Bergamota, Limón, Gálbano\n"
"• Corazón: Notas ozónicas, Salvia, Geranio\n"
"• Fondo: Pachulí, Vetiver, Musgo de roble, Haba tonka\n\n"
"CARACTERÍSTICAS\n"
"• Tamaño: 100ml / 3.4 oz\n"
"• Concentración: Parfum (extracto)\n"
"• Duración estimada: 8-12 horas\n"
"• Estela: media-alta\n"
"• Unisex: ideal para hombre y mujer\n"
"• Presentación: frasco original sellado con caja\n\n"
"100% original. Envío inmediato desde México. Garantía del vendedor 30 días."
)

payload={
  "title": TITLE,
  "category_id": cat,
  "price": PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes":[
    {"id":"BRAND","value_name":"Bharara"},
    {"id":"LINE","value_name":"Viking"},
    {"id":"MODEL","value_name":"Viking Beirut"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"FRAGRANCE_TYPE","value_name":"Parfum"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"VOLUME_CAPACITY","value_name":"100 mL"},
    {"id":"PRESENTATION_TYPE","value_name":"Estuche"},
    {"id":"MAIN_OLFACTIVE_FAMILY","value_name":"Aromática"},
    {"id":"INTENSITY","value_name":"Intensa"},
    {"id":"RECOMMENDED_USE_FRAGRANCE","value_name":"Diario"},
    {"id":"INCLUDES_REPLACEMENT","value_name":"No"},
    {"id":"PRODUCT_FEATURES","value_name":"Larga duración"},
    {"id":"COUNTRY_OF_ORIGIN","value_name":"Emiratos Árabes Unidos"}
  ],
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}

p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("\nPOST /items:",p.status_code)
print(p.text[:2000])
if p.status_code==201:
    d=p.json()
    iid=d.get("id")
    print(f"\n✅ CREATED {iid} @ ${PRICE} status={d.get('status')}")
    print(f"permalink: {d.get('permalink')}")
