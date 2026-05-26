import os, requests, time
import meli_token
API="https://api.mercadolibre.com"
ACCS=["JUAN","RAYMUNDO","YC_NEW","WILBERT","CLARIBEL","ASVA","BREN","ANGEL","ASGARI","RMAYCHI","AH","MC"]
total_ok=0; total_skip=0; total_err=0
for acc in ACCS:
    env=f"MELI_REFRESH_TOKEN_{acc}"
    rt=os.environ.get(env)
    if not rt: print(f"\n### {acc}: (sin secret, skip)"); continue
    AT=meli_token.refresh(rt).json().get("access_token")
    if not AT: print(f"### {acc}: AUTH_FAIL"); continue
    H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
    me=requests.get(f"{API}/users/me",headers=H,timeout=15).json(); uid=me.get("id")
    # paginar abiertos
    claims=[]; off=0
    while True:
        r=requests.get(f"{API}/post-purchase/v1/claims/search",params={"stage":"claim","status":"opened","players.role":"respondent","players.user_id":uid,"limit":50,"offset":off},headers=H,timeout=20).json()
        data=r.get("data") or r.get("results") or []
        claims+=data
        if len(data)<50: break
        off+=50
    print(f"\n### {acc} (uid {uid}): {len(claims)} reclamos abiertos")
    ok=skip=err=0
    for cl in claims:
        cid=cl.get("id")
        d=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15).json()
        seller_actions=[]
        for p in (d.get("players") or []):
            if p.get("role")=="respondent": seller_actions=[a.get("action") for a in (p.get("available_actions") or [])]
        if "refund" not in seller_actions:
            print(f"  SKIP {cid} reason={d.get('reason_id')} actions={seller_actions}"); skip+=1; continue
        rp=requests.post(f"{API}/post-purchase/v1/claims/{cid}/actions/refund",headers=HJ,timeout=30)
        if rp.status_code<300:
            print(f"  REFUND OK {cid} reason={d.get('reason_id')}"); ok+=1
        else:
            print(f"  REFUND ERR {cid} http={rp.status_code} {rp.text[:200]}"); err+=1
        time.sleep(0.2)
    print(f"  -> {acc}: refund_ok={ok} skip={skip} err={err}")
    total_ok+=ok; total_skip+=skip; total_err+=err
print(f"\n========== TOTAL OK={total_ok} SKIP={total_skip} ERR={total_err}")
print("DONE")
