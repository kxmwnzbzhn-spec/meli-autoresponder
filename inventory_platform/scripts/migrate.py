"""Migration runner — aplica SQL files en orden a Supabase."""
import os,glob,requests,sys
SUPABASE_URL=os.environ["SUPABASE_URL"]
SK=os.environ["SUPABASE_SERVICE_KEY"]
# Supabase REST API doesn't run raw SQL; use Postgres pooler via psycopg
import psycopg2
DSN=os.environ["SUPABASE_DB_URL"]  # postgres://postgres.xxx:pwd@aws-0-us-east-1.pooler.supabase.com:6543/postgres

files=sorted(glob.glob("inventory_platform/schema/*.sql"))
print(f"Found {len(files)} SQL files")
conn=psycopg2.connect(DSN)
conn.autocommit=False
cur=conn.cursor()
try:
    for f in files:
        sql=open(f).read()
        print(f"  applying {f} ({len(sql)} bytes)")
        cur.execute(sql)
    conn.commit()
    print("✓ migrations applied")
except Exception as e:
    conn.rollback()
    print(f"✗ migration error: {e}")
    sys.exit(1)
finally:
    cur.close(); conn.close()
