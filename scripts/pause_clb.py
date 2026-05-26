import os, requests
import meli_token
API="https://api.mercadolibre.com"
IDS=("5244434174,2890996849,2890989785,2890989209,2890988575,2890987863,2890987765,2890976191,"
     "2890975983,2890951427,2890950617,2890938767,2890938641,2890938557,2888494751,5245310498,"
     "2890952081,2890840987,5245310490,5245746252,5245546822,5245546756").split(",")
ids=["MLM"+i.strip() for i in IDS]
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
ok=err=skip=0
for iid in ids:
    try:
        b=requests.get(f"{API}/items/{iid}?attributes=status",headers=H,timeout=15).json()
        st=b.get("status")
        if st=="paused": print(f"  {iid} ya pausado"); skip+=1; continue
        if st in ("closed","under_review"): print(f"  {iid} status={st} (no pauseable)"); skip+=1; continue
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
        if r.status_code<300: print(f"  {iid} {st}->paused"); ok+=1
        else: print(f"  {iid} ERR http={r.status_code} {r.text[:140]}"); err+=1
    except Exception as e:
        print(f"  {iid} EXC {type(e).__name__}: {e}"); err+=1
print(f"\nOK={ok} SKIP={skip} ERR={err} total={len(ids)}")
print("DONE")
