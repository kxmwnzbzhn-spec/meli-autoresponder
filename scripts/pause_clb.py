import os, requests
import meli_token
IDS="5244434174,2890996849,2890989785,2890989209,2890988575,2890987863,2890987765,2890976191,2890975983,2890951427,2890950617,2890938767,2890938641,2890938557,2888494751,5245310498,2890952081,2890840987,5245310490".split(",")
ids=["MLM"+i for i in IDS]
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
ok=err=skip=0
for iid in ids:
    b=requests.get(f"{API}/items/{iid}?attributes=status,seller_id".replace("{API}","https://api.mercadolibre.com"),headers=H,timeout=15).json()
    st=b.get("status")
    if st=="paused": print(f"  {iid} ya pausado"); skip+=1; continue
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300: print(f"  {iid} {st}->paused"); ok+=1
    else: print(f"  {iid} ERR http={r.status_code} {r.text[:120]}"); err+=1
print(f"\nOK={ok} SKIP={skip} ERR={err} total={len(ids)}")
print("DONE")
