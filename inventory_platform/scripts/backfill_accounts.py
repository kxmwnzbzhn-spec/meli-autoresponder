"""Backfill: importa las 9 cuentas MELI a Supabase."""
import os,requests,psycopg2
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
DSN=os.environ["SUPABASE_DB_URL"]

ACCOUNTS=[
  ("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),
  ("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),
  ("Juan","MELI_REFRESH_TOKEN_JUAN"),
  ("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("Asva","MELI_REFRESH_TOKEN_ASVA"),
  ("Mildred","MELI_REFRESH_TOKEN_MILDRED"),
  ("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),
  ("Bren","MELI_REFRESH_TOKEN_BREN"),
]
conn=psycopg2.connect(DSN); cur=conn.cursor()
for nick,env in ACCOUNTS:
    rt=os.environ.get(env,"")
    if not rt:
        print(f"  {nick}: NO_TOKEN env={env}"); continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",
        data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
    T=r.get("access_token")
    if not T:
        print(f"  {nick}: AUTH_FAIL"); continue
    me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {T}"}).json()
    uid=me.get("id")
    if not uid:
        print(f"  {nick}: NO_UID"); continue
    cur.execute("""INSERT INTO accounts (nickname, meli_user_id, refresh_token_secret, active)
        VALUES (%s,%s,%s,true)
        ON CONFLICT (nickname) DO UPDATE SET meli_user_id=EXCLUDED.meli_user_id, refresh_token_secret=EXCLUDED.refresh_token_secret""",
        (nick,uid,env))
    print(f"  ✓ {nick} uid={uid}")
conn.commit(); cur.close(); conn.close()
print("✓ accounts backfilled")
