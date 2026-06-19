import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

# Map account → token env var
ACC_TO_KEY={"ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","WILBERT":"MELI_REFRESH_TOKEN_WILBERT","AH":"MELI_REFRESH_TOKEN_AH"}
TOKENS={}
for acct,k in ACC_TO_KEY.items():
  rt=os.environ.get(k)
  if not rt: continue
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
  if r.status_code<400: TOKENS[acct]=r.json()["access_token"]

CLAIMS=[
  ("ASVA",5526369459,"Bocina IP67 Rojo",249,"not_working_item","-3.8 días"),
  ("ASVA",5527830912,"Dashcam DVR-3",299,"repentant_buyer","-2.8 días"),
  ("ASVA",5527085525,"Dashcam DVR-3",398,"not_working_item","-2.8 días"),
  ("ASVA",5528532081,"Dashcam DVR-3",398,"not_working_item","-1.8 días"),
  ("ASVA",5529104767,"Buds 2",149,"not_working_item","-19h"),
  ("CLARIBEL",5524810394,"JBL Go 4 Rojo",549,"different_color_or_size","-19h"),
  ("CLARIBEL",5529820798,"JBL Go 3 Negro",398,"not_working_item","+4h"),
  ("CLARIBEL",5529258594,"JBL Clip 5 Azul",799,"not_working_item","+4h"),
  ("WILBERT",5524649191,"JBL Charge 6",1999,"repentant_buyer","+4h"),
  ("WILBERT",5522260719,"JBL Charge 6",1999,"repentant_buyer","+5h"),
  ("CLARIBEL",5530383971,"JBL Go 4 Camuflaje",555,"broken_item","+3d"),
  ("ASVA",5530536869,"Dashcam DVR-3",199,"not_working_item","+4d"),
  ("AH",5530747987,"Sony XB100",599,"damaged_package_broken_item","+4d"),
  ("ASVA",5530494201,"Dashcam DVR-3",199,"damaged_package_not_working_item","+4d"),
  ("ASVA",5530591691,"Bocina IP67 Morado",498,"not_working_item","+4d"),
  ("ASVA",5530689643,"Buds 2",149,"not_working_item","+5d"),
]

print(f"{'#':<3} {'acct':<10} {'claim':<11} {'STATUS':<10} {'STAGE':<10} {'SELLER ACTIONS':<40} ${'AMT':<5} {'product':<30} {'vence':<8}")
print("="*180)
for i,(acct,cid,prod,amt,reason,due) in enumerate(CLAIMS,1):
  AT=TOKENS.get(acct)
  if not AT:
    print(f"{i:<3} {acct:<10} {cid:<11} NO TOKEN")
    continue
  H={"Authorization":f"Bearer {AT}"}
  r=requests.get(f"{API}/post-purchase/v1/claims/{cid}",headers=H,timeout=15)
  if r.status_code!=200:
    print(f"{i:<3} {acct:<10} {cid:<11} HTTP {r.status_code}")
    continue
  c=r.json()
  status=c.get("status","?")
  stage=c.get("stage","?")
  seller_actions=[]
  for p in c.get("players",[]) or []:
    if p.get("role")=="respondent" or p.get("type")=="seller":
      seller_actions=p.get("available_actions",[])
  acts_str=str([a.get("action") if isinstance(a,dict) else a for a in seller_actions])[:38]
  recoverable="✓" if status=="opened" and seller_actions else "✗"
  print(f"{i:<3} {acct:<10} {cid:<11} {status:<10} {stage:<10} {acts_str:<40} {amt:<5} {prod[:28]:<30} {due:<8} {recoverable}")
