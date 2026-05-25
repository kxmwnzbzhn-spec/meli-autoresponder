"""
Crear catalog_suggestions ASVA para 3 bocinas Flipi7 35W IP67 (colores), reusando fotos de cada listing.
Items: MLM5233454100, MLM2886136351, MLM5233480022
"""
import os, json, hashlib, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json(); print("ASVA uid:",me.get("id"))

ITEMS=["MLM5233454100","MLM2886136351","MLM5233480022"]

def ean13(seed):
    h=hashlib.md5(seed.encode()).hexdigest(); n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
    b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b)); return b+str((10-(s%10))%10)

results=[]
for iid in ITEMS:
    print(f"\n{'='*60}\nITEM {iid}\n{'='*60}")
    it=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    title_o=it.get("title",""); print("listing:",title_o)
    color=None
    for a in it.get("attributes",[]):
        if a.get("id")=="COLOR": color=a.get("value_name")
    if not color:
        for c in ["Negro","Azul","Rojo","Morado","Lila","Verde","Rosa","Blanco","Gris","Naranja","Celeste"]:
            if c.lower() in title_o.lower(): color=c; break
    pics=[{"id":p["id"]} for p in (it.get("pictures") or []) if p.get("id")][:8]
    print(f"color={color} | fotos={len(pics)}")
    if not color or not pics:
        print("  ⚠ salto (sin color o sin fotos)"); results.append((iid,color,"SKIP")); continue
    color_adj={"Rojo":"Roja","Negro":"Negra","Morado":"Morada","Lila":"Lila","Blanco":"Blanca"}.get(color, color+"a" if color.endswith("o") else color)
    ean=ean13(f"asvaelectronics::flipi7::{color.lower()}")
    title=f"Bocina Bluetooth Portátil Asvaelectronics Flipi7 35W IP67 Resistente al Agua Bajos Potentes Inalámbrica {color_adj}"
    attrs=[
     {"id":"BRAND","values":[{"name":"Asvaelectronics"}]},
     {"id":"MODEL","values":[{"name":"Flipi7"}]},
     {"id":"ALPHANUMERIC_MODEL","values":[{"name":"Flipi7"}]},
     {"id":"COLOR","values":[{"name":color}]},
     {"id":"POWER_OUTPUT_RMS","values":[{"name":"35 W"}]},
     {"id":"WITH_BLUETOOTH","values":[{"name":"Sí"}]},
     {"id":"IS_PORTABLE","values":[{"name":"Sí"}]},
     {"id":"IS_WIRELESS","values":[{"name":"Sí"}]},
     {"id":"IS_WATERPROOF","values":[{"name":"Sí"}]},
     {"id":"IP_RATING","values":[{"name":"IP67"}]},
     {"id":"GTIN","values":[{"name":ean}]},
    ]
    body={"site_id":"MLM","domain_id":"MLM-SPEAKERS","type":"EDIT","title":title,"attributes":attrs,"pictures":pics}
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    print("POST http",r.status_code)
    try:
        rb=r.json(); sid=rb.get("id") or rb.get("suggestion_id"); st=rb.get("status")
        print(f"  -> id={sid} status={st}")
        if not sid: print("  body:",json.dumps(rb,ensure_ascii=False)[:500])
        results.append((iid,color,f"{sid} {st}"))
    except Exception:
        print("  raw:",r.text[:400]); results.append((iid,color,"ERR"))

print("\n\n===== RESUMEN =====")
for iid,color,res in results: print(f"  {iid} | {color} | {res}")
