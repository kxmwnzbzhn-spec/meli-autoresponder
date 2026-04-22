import os,requests,time,json,io
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

IID="MLM2883448187"

# GDrive file IDs → URL de descarga directa
GDRIVE=[
    "1xZ33_r6jngqHkAAdX0p29AdN3lmlJIx2",
    "1u6_6W4pBbW9-EL_YXs6lCqQjqw3iCVef",
    "1AS5RRWjMDCVxYRmw8361WeFz5GbmRA5E",
    "1-Pr5DSq9skitUkiFkeNQQOrRUNkUCv0j",
]

# 1) Descargar imagenes desde GDrive
print("=== Descargando imagenes ===")
imgs=[]
for fid in GDRIVE:
    url=f"https://drive.google.com/uc?export=download&id={fid}"
    r=requests.get(url,timeout=30,allow_redirects=True)
    if r.status_code==200 and len(r.content)>1000:
        # Verificar que es image
        ct=r.headers.get("content-type","")
        if "image" in ct or r.content[:4] in (b'\xff\xd8\xff\xe0',b'\xff\xd8\xff\xe1',b'\xff\xd8\xff\xdb',b'\x89PNG'):
            imgs.append(r.content)
            print(f"  OK {fid}: {len(r.content)} bytes, ct={ct}")
        else:
            # GDrive returned HTML (cookie/quota page) - try uc2 endpoint
            print(f"  HTML/err {fid}, intentando otra ruta...")
            url2=f"https://drive.usercontent.google.com/download?id={fid}&export=download&authuser=0"
            r=requests.get(url2,timeout=30,allow_redirects=True)
            if r.status_code==200 and len(r.content)>1000 and r.content[:4] in (b'\xff\xd8\xff\xe0',b'\xff\xd8\xff\xe1',b'\xff\xd8\xff\xdb',b'\x89PNG'):
                imgs.append(r.content)
                print(f"    OK alt {fid}: {len(r.content)} bytes")
            else:
                print(f"    FAIL {fid}")
    else:
        print(f"  ERR {fid}: {r.status_code}")

if not imgs:
    print("SIN IMAGENES - abort")
    raise SystemExit(1)

# 2) Subir a MELI - usar endpoint /pictures con multipart
print(f"\n=== Subiendo {len(imgs)} imagenes a MELI ===")
pic_ids=[]
for idx,img in enumerate(imgs):
    files={"file":(f"aqua_{idx}.jpg",img,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures",headers={"Authorization":f"Bearer {TOKEN}"},files=files,timeout=60)
    if r.status_code in (200,201):
        pid=r.json().get("id")
        pic_ids.append(pid)
        print(f"  OK pic{idx}: {pid}")
    else:
        print(f"  ERR pic{idx}: {r.status_code} {r.text[:200]}")
    time.sleep(1)

if not pic_ids:
    print("SIN PIC IDS - abort")
    raise SystemExit(1)

# 3) Agregar variante Aqua al item MLM2883448187
print(f"\n=== Agregando variante Aqua con {len(pic_ids)} fotos ===")
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_variations=it.get("variations",[])
print(f"Variantes actuales: {len(current_variations)}")

# Construir lista con las existentes + nueva
new_vars=[]
for v in current_variations:
    nv={
        "id":v.get("id"),
        "price":v.get("price"),
        "available_quantity":v.get("available_quantity"),
        "attribute_combinations":v.get("attribute_combinations",[])
    }
    if v.get("picture_ids"):
        nv["picture_ids"]=v["picture_ids"]
    new_vars.append(nv)

# Agregar Aqua
new_vars.append({
    "price":499,
    "available_quantity":1,
    "attribute_combinations":[{"id":"COLOR","value_name":"Aqua"}],
    "picture_ids":pic_ids[:10]
})

r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"variations":new_vars},timeout=30)
print(f"PUT variations: {r.status_code}")
if r.status_code not in (200,201):
    print(f"  err: {r.text[:500]}")
else:
    resp=r.json()
    print(f"  nueva lista variations: {len(resp.get('variations',[]))}")
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=ac[0].get("value_name","") if ac else ""
        print(f"    var={v.get('id')} {col} qty={v.get('available_quantity')}")
    
    # Actualizar stock_config
    with open("stock_config.json") as f: sc=json.load(f)
    if IID in sc:
        vars_cfg=sc[IID].setdefault("variations",{})
        vars_cfg["Aqua"]={"stock":1037,"orig_id":"MLM2747271435"}
        sc[IID]["real_stock"]=sum(v.get("stock",0) for v in vars_cfg.values())
    with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
    print(f"stock_config: total {sc[IID]['real_stock']}")
