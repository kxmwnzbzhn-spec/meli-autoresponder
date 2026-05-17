"""CLI: registra ajuste manual de stock.
Usage: SKU=X WAREHOUSE=bodega_main DELTA=-5 REASON='merma' AUTHOR=luis python manual_adjust.py
"""
import os,psycopg2
DSN=os.environ["SUPABASE_DB_URL"]
sku=os.environ["SKU"]; wh=os.environ.get("WAREHOUSE","bodega_main")
delta=int(os.environ["DELTA"]); reason=os.environ["REASON"]; author=os.environ.get("AUTHOR","manual")
conn=psycopg2.connect(DSN); cur=conn.cursor()
cur.execute("SELECT apply_stock_delta(%s,%s,%s,%s,NULL,NULL,NULL,NULL,%s,%s)",(sku,wh,delta,'manual_in' if delta>0 else 'manual_out',reason,author))
mid=cur.fetchone()[0]
cur.execute("INSERT INTO manual_adjustments (sku,warehouse,delta,reason,author,applied_movement_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",(sku,wh,delta,reason,author,mid))
aid=cur.fetchone()[0]
conn.commit(); print(f"adjustment {aid} applied (movement_id={mid})")
