#!/usr/bin/env python3
"""War Yiriam V5 — DINAMICO + pulido.
Cambios vs v4:
- Auto-descubre TODOS los items active con catalog_product_id (no lista hardcoded).
  → auto-incluye nuevos, auto-excluye cerrados. Cero lista que mantener.
- Respeta PAUSED_LOCK, FLOOR_OVERRIDE, CEILING_OVERRIDE.
- Lógica por item:
    not_listed       → reindex bump alternado (±1) para forzar re-eval MELI
    winning/sharing  → max-up a low_ext-5 si hay headroom; si no, hold (nunca baja por gusto)
    competing/losing → ptw-2 (toma buy box aun contra fantasma Lider Platino), respeta floor
- Error handling por item (un fallo no tumba la corrida).
- Reporte con conteo winning/competing/reindex.
"""
import os, time, requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

# Items que NO se tocan (pausados manual por el usuario)
PAUSED_LOCK={"MLM5353056250"}

# Pisos por item (no bajar de aquí)
FLOOR_OVERRIDE={
  "MLM5390346898":349,
  "MLM5390372034":349,
  "MLM5364336572":899,
  "MLM5291785036":499,
  "MLM5291774150":499,
  "MLM2909183147":499,
  "MLM2950827385":499,
  "MLM5390371996":499,
  "MLM2950790153":499,
  "MLM2950790159":499,
  "MLM2950790163":499,
  "MLM2950827361":499,
}
# Techos por item (no subir de aquí)
CEILING_OVERRIDE={
  "MLM5363034838":899,
  "MLM5364336572":999,
  "MLM5291785036":549,
  "MLM5291774150":549,
  "MLM2909183147":549,
  "MLM2950827385":549,
  "MLM5390371996":549,
  "MLM2950790153":549,
  "MLM2950790159":549,
  "MLM2950790163":549,
  "MLM2950827361":549,
}

def tok():
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# DESCUBRIR todos los active
ids=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    ids.extend(res)
    if len(res)<50 or offset>1000: break
    offset+=50

acts=[]; stat={"win":0,"comp":0,"reindex":0,"locked":0,"nocpid":0,"err":0}
for iid in ids:
    if iid in PAUSED_LOCK:
        stat["locked"]+=1; continue
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=12).json()
        if g.get("status")!="active": continue
        cur=g.get("price"); cpid=g.get("catalog_product_id"); title=(g.get("title") or "")[:20]
        if not cpid:
            stat["nocpid"]+=1; continue
        floor=FLOOR_OVERRIDE.get(iid,MIN_FLOOR); ceil=CEILING_OVERRIDE.get(iid,999999)

        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        pst=(p.get("status") or "").lower(); ptw=p.get("price_to_win")

        # low_ext (competidor más barato, excluyéndonos)
        low_ext=None
        try:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
            xs=[]
            for rr in (pr.get("results") or []):
                rid=rr.get("item_id") or rr.get("id"); rp=rr.get("price")
                rst=(rr.get("status") or "active").lower(); rq=rr.get("available_quantity",1)
                if rid and rid!=iid and rp and rst=="active" and rq>0: xs.append(rp)
            xs.sort()
            if xs: low_ext=xs[0]
        except: pass

        target=None; reason=""
        if pst=="not_listed":
            stat["reindex"]+=1
            bump = cur-1 if cur>floor else cur+1
            target=bump; reason="reindex_bump"
        elif pst in ("winning","sharing_first_place"):
            stat["win"]+=1
            if low_ext:
                up=min(int(low_ext)-5, ceil); up=max(up,floor)
                if up>cur: target=up; reason=f"max-up low_ext={low_ext}"
                else: reason=f"hold (low_ext={low_ext})"
            else:
                reason="hold (sin comp)"
        elif pst in ("competing","losing"):
            stat["comp"]+=1
            base = int(ptw) if ptw else (int(low_ext) if low_ext else None)
            if base:
                t=max(base-2,floor); t=min(t,ceil)
                if t<cur: target=t; reason=f"CLAIM ptw={ptw} low_ext={low_ext}"
                else: reason=f"floor=${floor} bloquea (ptw={ptw})"
            else:
                reason="sin ptw/low_ext"
        else:
            reason=f"st={pst} skip"

        if target is not None and target!=cur:
            r2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=15)
            acts.append(f"{iid} '{title}' ${cur}→${target} [{reason}] http={r2.status_code}")
        else:
            acts.append(f"{iid} '{title}' hold ${cur} [{reason}]")
        time.sleep(0.2)
    except Exception as e:
        stat["err"]+=1
        acts.append(f"ERR {iid}: {e}")

print(f"war-yiriam-v5: descubiertos={len(ids)} | WIN={stat['win']} COMP(fix)={stat['comp']} REINDEX={stat['reindex']} LOCKED={stat['locked']} sin_cpid={stat['nocpid']} ERR={stat['err']}")
for a in acts: print(f"  {a}")
