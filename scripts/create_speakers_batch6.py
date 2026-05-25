"""
Crear catalog_suggestions ASVA para 6 bocinas, leyendo color/potencia reales de cada listing.
Items: 5235934132,5235934150,2886523697,5235934108,2886523677,5235946486
"""
import os, json, hashlib, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print("ASVA uid:", requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

ITEMS=["MLM5235934132","MLM5235934150","MLM2886523697","MLM5235934108","MLM2886523677","MLM5235946486"]

def ean13(seed):
    h=hashlib.md5(seed.encode()).hexdigest(); n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
    b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b)); return b+str((10-(s%10))%10)

def getattr_(it,aid):
    for a in it.get("attributes",[]):
        if a.get("id")==aid: return a.get("value_name")
    return None

results=[]
for iid in ITEMS:
    print(f"\n{'='*60}\nITEM {iid}")
    it=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    if it.get("error") or not it.get("id"):
        print("  no existe:",str(it)[:150]); results.append((iid,"?","NO_ITEM")); continue
    title_o=it.get("title",""); dom=it.get("domain_id"); print("listing:",title_o,"| dom:",dom)
    color=getattr_(it,"COLOR")
    if not color:
        for c in ["Negro","Azul","Rojo","Morado","Lila","Verde","Rosa","Blanco","Gris","Naranja","Celeste","Camuflaje"]:
            if c.lower() in title_o.lower(): color=c; break
    power=getattr_(it,"POWER_OUTPUT_RMS") or "35 W"
    pics=[{"id":p["id"]} for p in (it.get("pictures") or []) if p.get("id")][:8]
    print(f"  color={color} | power={power} | fotos={len(pics)}")
    if not color or not pics:
        print("  ⚠ SKIP (sin color o fotos)"); results.append((iid,color,"SKIP")); continue
    color_adj={"Rojo":"Roja","Negro":"Negra","Morado":"Morada","Blanco":"Blanca"}.get(color, color)
    pw_num="".join(ch for ch in power if ch.isdigit()) or "35"
    ean=ean13(f"asvaelectronics::flipi7::{color.lower()}::{pw_num}")
    title=f"Bocina Bluetooth Portátil Asvaelectronics Flipi7 {pw_num}W IP67 Resistente al Agua Bajos Potentes Inalámbrica {color_adj}"
    attrs=[
     {"id":"BRAND","values":[{"name":"Asvaelectronics"}]},
     {"id":"MODEL","values":[{"name":"Flipi7"}]},
     {"id":"ALPHANUMERIC_MODEL","values":[{"name":"Flipi7"}]},
     {"id":"COLOR","values":[{"name":color}]},
     {"id":"POWER_OUTPUT_RMS","values":[{"name":f"{pw_num} W"}]},
     {"id":"WITH_BLUETOOTH","values":[{"name":"Sí"}]},
     {"id":"IS_PORTABLE","values":[{"name":"Sí"}]},
     {"id":"IS_WIRELESS","values":[{"name":"Sí"}]},
     {"id":"IS_WATERPROOF","values":[{"name":"Sí"}]},
     {"id":"IP_RATING","values":[{"name":"IP67"}]},
     {"id":"GTIN","values":[{"name":ean}]},
    ]
    body={"site_id":"MLM","domain_id":dom or "MLM-SPEAKERS","type":"EDIT","title":title,"attributes":attrs,"pictures":pics}
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    try:
        rb=r.json(); sid=rb.get("id") or rb.get("suggestion_id"); st=rb.get("status")
        print(f"  POST {r.status_code} -> id={sid} status={st}")
        if not sid: print("  body:",json.dumps(rb,ensure_ascii=False)[:400])
        results.append((iid,f"{color} {pw_num}W",f"{sid} {st}"))
    except Exception:
        print("  raw:",r.text[:300]); results.append((iid,color,"ERR"))

print("\n\n===== RESUMEN =====")
for iid,c,res in results: print(f"  {iid} | {c} | {res}")
