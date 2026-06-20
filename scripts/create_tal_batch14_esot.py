"""
Replicar 14 catalog_products TAL en MLM-ESOTERIC_PERFUMES, cuenta ADRIAN.
Reusa título y fotos del catalog product de referencia. Genera EAN único por item.
"""
import os, json, hashlib, requests, time, re
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("Adrian uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

IDS=["MLM70245995","MLM70246250","MLM70246080","MLM52129383","MLM70112010",
     "MLM70063829","MLM70063831","MLM70063753","MLM70064197","MLM70063777",
     "MLM69963991","MLM69794759","MLM69794803","MLM69795006"]

def ean13(seed):
    h=hashlib.md5(seed.encode()).hexdigest()
    n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
    b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
    return b+str((10-(s%10))%10)

def desc_for(name):
    # extraer nombre limpio (e.g. "Sombra del Jaguar")
    m=re.search(r"Perfume\s+(.+?)\s+The Alchemia Lab", name)
    pname = m.group(1) if m else "Piedra de la colección"
    return (f"{pname} de The Alchemia Lab — perfume de la colección México en la Piel. Eau de Parfum 100 ml unisex, "
            f"elaboración artesanal mexicana de Yucatán. Aroma de carácter distintivo, parte de la línea de perfumería "
            f"de autor inspirada en la naturaleza, los rituales y la cosmovisión mexicana.\n\n"
            f"DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Nombre: {pname}\n"
            f"• Eau de Parfum 100 ml\n• Unisex\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
            f"CARÁCTER\nPerfume de autor con identidad mexicana, ideal para amantes de fragancias nicho de carácter, "
            f"con narrativa olfativa propia y notas seleccionadas.\n\n"
            f"PRESENTACIÓN\nBotella ámbar con etiquetado artesanal. Eau de Parfum, formato spray, 100 ml.")

results=[]
for cid in IDS:
    print(f"\n========== {cid} ==========")
    r=requests.get(f"{API}/products/{cid}",headers=H,timeout=15)
    if r.status_code!=200:
        print(f"  GET FAIL {r.status_code}"); results.append((cid,None,"get_fail"))
        continue
    p=r.json()
    title=p.get("name","").strip()
    print(f"  title: {title[:90]}")
    pics_src=p.get("pictures") or []
    # reusar URLs sin re-upload
    pics=[{"url":pp.get("secure_url") or pp.get("url")} for pp in pics_src[:6] if pp.get("secure_url") or pp.get("url")]
    print(f"  fotos:{len(pics)}")
    # extraer nombre del perfume para MODEL
    m=re.search(r"Perfume\s+(.+?)\s+The Alchemia Lab", title)
    perfume_name = m.group(1) if m else "TAL Edición"
    model_val = f"{perfume_name} 100ml"
    ean = ean13(f"adrian::tal::{perfume_name}::esot::100ml::v1")
    print(f"  EAN:{ean}  MODEL:{model_val}")
    ATTRS=[
     {"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
     {"id":"MODEL","values":[{"name":model_val}]},
     {"id":"GTIN","values":[{"name":ean}]},
     {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
    ]
    body={"site_id":"MLM","domain_id":"MLM-ESOTERIC_PERFUMES","type":"EDIT","title":title,"attributes":ATTRS,"pictures":pics}
    rp=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    print(f"  POST {rp.status_code}")
    rb=rp.json()
    sid=rb.get("id") or rb.get("suggestion_id")
    if sid:
        print(f"  >>> NEW SID = {sid}  status={rb.get('status')}")
        time.sleep(3)
        rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":desc_for(title)},timeout=20)
        print(f"  desc {rd.status_code}")
        results.append((cid,sid,rb.get('status')))
    else:
        err=json.dumps(rb,ensure_ascii=False)[:400]
        print(f"  ERR body: {err}")
        results.append((cid,None,err[:120]))
    time.sleep(2)

print("\n\n========== RESUMEN ==========")
for cid,sid,st in results:
    print(f"  {cid}  →  {sid or 'FAIL'}  {st}")
