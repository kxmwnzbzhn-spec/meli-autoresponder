"""
Distribuir 12 catalog products TAL en 6 cuentas (2 c/u) en MLM-ESOTERIC_PERFUMES.
Restantes 2 quedan para 24h (cuando se libere cuota).

Distribución:
  MAYRELY (local)  — MLM70245995 Corazón de Copal,  MLM70246250 Sombra del Jaguar
  WILBERT (worker) — MLM70246080 Mandarin Quetzal,   MLM52129383 Tláloc Intenso
  CLARIBEL(worker) — MLM70112010 Cenote Azul,        MLM70063829 Quinto Aliento
  RAYMUNDO(worker) — MLM70063831 Xibalbá Royal,      MLM70063753 Fuerza de Kukulcán
  ASGARI  (local)  — MLM70064197 Manantial Valle Real, MLM70063777 Flor de la Noche
  JUAN    (worker) — MLM69963991 Luz del Desierto,   MLM69794759 Rosa del Viento
  --- 24H pendientes:
  MLM69794803 Dark Oud Cacao,  MLM69795006 Dominio del Fuego
"""
import os, json, hashlib, requests, time, re, sys
sys.path.insert(0, "scripts")
import meli_token

API = "https://api.mercadolibre.com"

PLAN = [
    ("MLM70245995", "MAYRELY"),
    ("MLM70246250", "MAYRELY"),
    ("MLM70246080", "WILBERT"),
    ("MLM52129383", "WILBERT"),
    ("MLM70112010", "CLARIBEL"),
    ("MLM70063829", "CLARIBEL"),
    ("MLM70063831", "RAYMUNDO"),
    ("MLM70063753", "RAYMUNDO"),
    ("MLM70064197", "ASGARI"),
    ("MLM70063777", "ASGARI"),
    ("MLM69963991", "JUAN"),
    ("MLM69794759", "JUAN"),
]
WORKER = {"WILBERT","YC_NEW","JUAN","RAYMUNDO","CLARIBEL","ASVA","BREN"}

def ean13(seed):
    h=hashlib.md5(seed.encode()).hexdigest()
    n="".join(c for c in h if c.isdigit())[:9].ljust(9,"0")
    b="290"+n; s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(b))
    return b+str((10-(s%10))%10)

def desc_for(name):
    m=re.search(r"Perfume\s+(.+?)\s+The Alchemia Lab", name)
    pname = m.group(1) if m else "Edición"
    return (f"{pname} de The Alchemia Lab — perfume de la colección México en la Piel. Eau de Parfum 100 ml unisex, "
            f"elaboración artesanal mexicana de Yucatán. Aroma de carácter distintivo, parte de la línea de perfumería "
            f"de autor inspirada en la naturaleza, los rituales y la cosmovisión mexicana.\n\n"
            f"DETALLES\n• Marca: The Alchemia Lab\n• Colección: México en la Piel\n• Nombre: {pname}\n"
            f"• Eau de Parfum 100 ml\n• Unisex\n• Origen: Yucatán, México\n• Elaboración artesanal\n\n"
            f"CARÁCTER\nPerfume de autor con identidad mexicana, ideal para amantes de fragancias nicho de carácter, "
            f"con narrativa olfativa propia y notas seleccionadas.\n\n"
            f"PRESENTACIÓN\nBotella ámbar con etiquetado artesanal. Eau de Parfum, formato spray, 100 ml.")

# cache de access tokens por cuenta
TOKEN_CACHE = {}
def at_for(account):
    if account in TOKEN_CACHE: return TOKEN_CACHE[account]
    if account in WORKER:
        at = meli_token.get_access_token(account)
    else:
        env = f"MELI_REFRESH_TOKEN_{account}"
        rt = os.environ.get(env)
        if not rt:
            raise RuntimeError(f"no env {env}")
        at = meli_token.refresh(rt)["access_token"]
    TOKEN_CACHE[account] = at
    return at

results = []
for cid, account in PLAN:
    print(f"\n========== {cid} → {account} ==========")
    try:
        AT = at_for(account)
    except Exception as e:
        print(f"  TOKEN FAIL: {e}")
        results.append((cid, account, None, f"token:{e}"))
        continue
    H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
    r=requests.get(f"{API}/products/{cid}",headers=H,timeout=15)
    if r.status_code!=200:
        print(f"  GET FAIL {r.status_code}")
        results.append((cid,account,None,f"get:{r.status_code}"))
        continue
    p=r.json()
    title=p.get("name","").strip()
    print(f"  title: {title[:80]}")
    pics_src=p.get("pictures") or []
    pics=[]
    for idx,pp in enumerate(pics_src[:6]):
        u = pp.get("secure_url") or pp.get("url")
        if not u: continue
        try:
            img=requests.get(u,timeout=60).content
            rpi=requests.post(f"{API}/pictures/items/upload",headers=H,
                files={"file":(f"{cid}_{idx}.jpg",img,"image/jpeg")},timeout=120)
            if rpi.status_code in (200,201):
                pics.append({"id":rpi.json()["id"]})
            else:
                print(f"    pic[{idx}] upload {rpi.status_code}: {rpi.text[:120]}")
        except Exception as e:
            print(f"    pic[{idx}] err: {e}")
    print(f"  fotos:{len(pics)}")
    m=re.search(r"Perfume\s+(.+?)\s+The Alchemia Lab", title)
    perfume_name = m.group(1) if m else "TAL"
    model_val = f"{perfume_name} 100ml"
    ean = ean13(f"{account.lower()}::tal::{perfume_name}::esot::100ml::v1")
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
        print(f"  >>> SID = {sid}  status={rb.get('status')}")
        time.sleep(3)
        rd=requests.post(f"{API}/catalog_suggestions/{sid}/description",headers=HJ,json={"plain_text":desc_for(title)},timeout=20)
        print(f"  desc {rd.status_code}")
        results.append((cid,account,sid,rb.get('status')))
    else:
        err=json.dumps(rb,ensure_ascii=False)[:300]
        print(f"  ERR: {err}")
        results.append((cid,account,None,err[:160]))
    time.sleep(2)

print("\n\n========== RESUMEN ==========")
ok=fail=0
for cid,acc,sid,st in results:
    flag="OK" if sid else "FAIL"
    if sid: ok+=1
    else: fail+=1
    print(f"  [{flag}] {cid:14s} {acc:9s} → {sid or '-'}  {st}")
print(f"\nTOTAL OK={ok} FAIL={fail}")
print("\nPendientes 24h:  MLM69794803 (Dark Oud Cacao),  MLM69795006 (Dominio del Fuego)")
