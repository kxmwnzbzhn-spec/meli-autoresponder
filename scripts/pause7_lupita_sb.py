import os, requests
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
H={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}

ITEMS=[
  ("MLM5633125272","Bocina Charge 6 IP67 30W Negro (trad)"),
  ("MLM5633125266","Bocina Bass 35W Negro (trad)"),
  ("MLM5633125276","Bocina Clip 5 IP67 Negro (trad)"),
  ("MLM5633125256","Bocina Bass 35W Rojo (trad)"),
  ("MLM5633129252","CK Boxers S"),
  ("MLM5633116342","CK Boxers M"),
  ("MLM5633091126","CK Boxers L"),
]
for iid,name in ITEMS:
  requests.delete(f"{SB}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=H,timeout=8)
  r=requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=H,
    json={"item_id":iid,"reason":f"Pausado por usuario Lupita 2026-07-03 - {name} - NO REACTIVAR"},timeout=8)
  print(f"{iid}: no_replenish {r.status_code}")

r=requests.post(f"{SB}/rest/v1/meli_user_directives",headers=H,
  json={"account":"LUPITA","scope":"batch","scope_value":"pause_7_bocinas_boxers","directive_type":"pause","raw_user_message":"pausa el lupita esto. 5633125272, 5633125266, boxer, 5633125276, 5633125256"},timeout=8)
print("directive:",r.status_code)
