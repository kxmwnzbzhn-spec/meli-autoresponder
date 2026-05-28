"""sync_supabase_to_meli_configs.py — Casa Supabase con stock_config_*.json del repo.

Supabase es la fuente de verdad global del stock físico. Este script:
  1. Lee stock real por SKU desde Supabase (sumando bodegas).
  2. Lee los stock_config_*.json existentes del otro motor (Wilbert, Asva, Claribel, etc.).
  3. Para cada MLM en cada config, busca su SKU (vía listings de Supabase) y actualiza:
     - real_stock = stock global del SKU
     - master_stock = max(master_stock_actual, stock_global)  (no baja master, solo sube si recibimos más)
     - active = (stock_global > 0)
     - agotado = (stock_global == 0)
     - last_sold = se conserva tal cual
  4. Si hubo cambios, sobreescribe el .json en disco (el workflow después hace git commit + push).

  Esto hace que el motor existente del otro Cowork (workflows de replenish, throttle, sales_cap)
  respete automáticamente nuestro stock físico unificado. Si un SKU se queda en 0 globalmente,
  TODOS los configs lo marcan inactivo y los replenish dejan de reactivar el listing en MELI.

  Multi-cuenta: el mismo SKU compartido entre cuentas verá el mismo real_stock global en todos
  los configs (no se distribuye). Esto evita la sobreventa cruzada entre cuentas.

Uso:
    SUPABASE_DB_URL=... python sync_supabase_to_meli_configs.py [--dry-run] [--repo-root .]
"""
import os, sys, json, argparse, glob, psycopg2
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repo-root", default=".", help="ruta a la raíz del repo (donde están stock_config_*.json)")
    args = ap.parse_args()

    DSN = os.environ["SUPABASE_DB_URL"]
    conn = psycopg2.connect(DSN); conn.autocommit = True; cur = conn.cursor()

    # 1. Stock real por SKU (suma TODAS las bodegas: electronica + perfume + devolucion + full_*)
    cur.execute("SELECT sku, SUM(qty)::int FROM stock GROUP BY sku")
    sku_stock_global = {r[0]: int(r[1] or 0) for r in cur.fetchall()}
    print(f"📦 SKUs con stock en Supabase: {len(sku_stock_global)}")

    # 2. Map MLM → SKU desde listings
    cur.execute("SELECT mlm_id, sku, account_id FROM listings")
    mlm_to_sku = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    print(f"🔗 listings totales en sistema: {len(mlm_to_sku)}")

    # 3. Pre-cálculo: número de listings ACTIVE por SKU (todas las cuentas)
    #    Esto cierra el edge case: stock=2 pero 3 listings activos → MELI mostraría 3 disponibles.
    cur.execute("""SELECT sku, COUNT(*) FROM listings
                   WHERE status='active' AND sku IS NOT NULL GROUP BY sku""")
    active_listings_per_sku = {r[0]: int(r[1]) for r in cur.fetchall()}
    # Set de "MLMs sobrantes que hay que pausar" (orden: priorizamos pausar listings recién creados / con menos ventas)
    sku_over = {}  # sku -> cuántos hay que pausar
    for sku, n_active in active_listings_per_sku.items():
        stock = sku_stock_global.get(sku, 0)
        if n_active > stock:
            sku_over[sku] = n_active - stock
    print(f"⚠ SKUs con MÁS listings activos que stock global: {len(sku_over)}")
    if sku_over:
        for s, n in list(sku_over.items())[:10]:
            print(f"   {s}: {active_listings_per_sku[s]} activos vs stock {sku_stock_global.get(s,0)} → pausar {n}")

    # Para decidir qué listings sobrantes pausar: tomamos por SKU los listings ordenados por last_sync DESC
    # y los primeros (más recientes/peor) son los candidatos a pausar
    cur.execute("""SELECT sku, mlm_id, account_id FROM listings
                   WHERE status='active' AND sku IS NOT NULL
                   ORDER BY sku, COALESCE(last_sync, '1970-01-01') DESC""")
    over_to_pause = set()  # mlm_ids que hay que pausar por excedente
    grouped = {}
    for sku, mlm, aid in cur.fetchall():
        grouped.setdefault(sku, []).append(mlm)
    for sku, n_over in sku_over.items():
        for mlm in grouped.get(sku, [])[:n_over]:
            over_to_pause.add(mlm)
    print(f"   total MLMs marcados como excedente: {len(over_to_pause)}")

    # 4. Iterar stock_config_*.json
    configs_path = os.path.join(args.repo_root, "stock_config_*.json")
    config_files = sorted(glob.glob(configs_path))
    if not config_files:
        print(f"⚠ No se encontraron archivos en {configs_path}")
        sys.exit(0)

    print(f"📄 configs encontrados: {len(config_files)}")
    total_changes = 0
    total_paused = 0
    total_reactivated = 0
    total_unknown_sku = 0
    summary_per_file = {}

    for path in config_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ✗ {path}: read error {e}")
            continue

        changes = 0; paused = 0; reactivated = 0; unknown_sku = 0; meta_present = "_meta" in data

        # iterar todas las claves que parezcan MLM
        for key, item in list(data.items()):
            if not isinstance(item, dict) or not key.startswith("MLM"):
                continue
            mlm = key
            mapping = mlm_to_sku.get(mlm)
            if not mapping:
                unknown_sku += 1
                continue
            sku, _ = mapping
            global_stock = sku_stock_global.get(sku, 0)

            # estado anterior
            old_real = item.get("real_stock", item.get("stock"))
            old_master = item.get("master_stock", item.get("max_stock", old_real or 0))
            old_active = item.get("active", True)
            old_agotado = item.get("agotado", False)

            # nuevo estado: real = stock global; master = max(viejo, real)
            new_real = global_stock
            new_master = max(int(old_master or 0), new_real)
            # Si este listing está en la lista de "excedentes" (más listings activos que stock),
            # se marca como inactivo/agotado para que MELI no muestre más de lo que hay
            is_overflow = mlm in over_to_pause
            new_active = (new_real > 0) and (not is_overflow)
            new_agotado = (new_real == 0) or is_overflow

            # detectar transiciones
            file_changed = False
            if old_real != new_real:
                item["real_stock"] = new_real
                if "stock" in item: item["stock"] = new_real
                file_changed = True
            if old_master != new_master:
                item["master_stock"] = new_master
                if "max_stock" in item: item["max_stock"] = new_master
                file_changed = True
            if old_active != new_active:
                item["active"] = new_active
                if new_active and not old_active: reactivated += 1
                file_changed = True
            if old_agotado != new_agotado:
                item["agotado"] = new_agotado
                if new_agotado and not old_agotado: paused += 1
                file_changed = True
            # Garantizar min_visible y available_quantity para listings activos
            if new_active:
                if item.get("min_visible") is None and "min_visible_stock" in item:
                    pass  # respetar el campo existente
                else:
                    item.setdefault("min_visible", 1)
                item.setdefault("available_quantity", 1)
                item.setdefault("auto_replenish", True)
            # Anotar SKU para trazabilidad
            if item.get("sku") != sku:
                item["sku"] = sku
                file_changed = True

            if file_changed: changes += 1

        # actualizar _meta
        if meta_present and isinstance(data.get("_meta"), dict):
            data["_meta"]["synced_from_supabase_at"] = datetime.now(timezone.utc).isoformat()

        summary_per_file[path] = (changes, paused, reactivated, unknown_sku)
        total_changes += changes; total_paused += paused; total_reactivated += reactivated; total_unknown_sku += unknown_sku

        if changes > 0 and not args.dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # 4. Reporte
    print("\n=== Resumen por archivo ===")
    for path, (chg, pau, rea, unk) in sorted(summary_per_file.items()):
        name = os.path.basename(path).replace("stock_config_","").replace(".json","")
        if chg or pau or rea or unk:
            print(f"  {name:<14} changes={chg:>4}  pause={pau:>3}  react={rea:>3}  no-sku-en-supabase={unk:>3}")

    print(f"\n=== TOTAL ===")
    print(f"  cambios aplicados: {total_changes}")
    print(f"  marcados agotado (real_stock=0): {total_paused}")
    print(f"  re-marcados disponibles (volvió stock): {total_reactivated}")
    print(f"  MLMs sin SKU mapeado en Supabase: {total_unknown_sku}")
    print(f"  modo: {'DRY-RUN (nada escrito)' if args.dry_run else 'APLICADO (archivos modificados)'}")

    cur.close(); conn.close()


if __name__ == "__main__":
    main()
