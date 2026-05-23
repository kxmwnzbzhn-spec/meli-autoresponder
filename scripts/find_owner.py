"""Prueba cada cuenta contra la app para hallar al dueño real."""
import os, requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
APP="5211907102822632"
ACCTS={
 "YC_NEW/YIRIAM":"MELI_REFRESH_TOKEN_YC_NEW","WILBERT":"MELI_REFRESH_TOKEN_WILBERT",
 "RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO","JUAN":"MELI_REFRESH_TOKEN_JUAN",
 "CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","ASVA":"MELI_REFRESH_TOKEN_ASVA",
 "DILCIE":"MELI_REFRESH_TOKEN_DILCIE","BREN":"MELI_REFRESH_TOKEN_BREN",
 "MILDRED":"MELI_REFRESH_TOKEN_MILDRED","MG20260424":"MELI_REFRESH_TOKEN_MG20260424",
}
for name,env in ACCTS.items():
    rt=os.environ.get(env)
    if not rt:
        print(f"{name}: sin token en secrets"); continue
    try:
        tk=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()
        T=tk.get("access_token")
        if not T:
            print(f"{name}: token inválido ({tk.get('message','?')})"); continue
        me=requests.get(f"{API}/users/me",headers={"Authorization":f"Bearer {T}"},timeout=10).json()
        uid=me.get("id"); nick=me.get("nickname")
        # GET application con token de usuario
        r=requests.get(f"{API}/applications/{APP}",headers={"Authorization":f"Bearer {T}"},timeout=10)
        owner=None
        try: owner=r.json().get("owner_id")
        except: pass
        es_dueno = (owner==uid)
        print(f"{name}: uid={uid} nick={nick} | GET app http={r.status_code} owner_id={owner} {'<<< DUEÑO' if es_dueno else ''}")
    except Exception as e:
        print(f"{name}: ERR {e}")
