-- =====================================================================
-- Warehouse routing por listing — separa inventario devolucion vs main
-- =====================================================================
-- Listings de espejo/reacondicionada/caja-abierta = ventas de DEVOLUCIONES
-- que se revendieron. Decremento debe ir a stock.warehouse='devolucion',
-- no a 'bodega_main'. Mismo SKU (mismo producto físico), diferente pool.
--
-- Listings normales (color directo): warehouse_default='bodega_main'
-- Listings de devolución: warehouse_default='devolucion'
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. Columnas warehouse_default
-- ---------------------------------------------------------------------
ALTER TABLE listings
    ADD COLUMN IF NOT EXISTS warehouse_default text NOT NULL DEFAULT 'bodega_main';

ALTER TABLE listing_variations
    ADD COLUMN IF NOT EXISTS warehouse_default text NOT NULL DEFAULT 'bodega_main';

CREATE INDEX IF NOT EXISTS idx_listings_warehouse_default ON listings(warehouse_default);
CREATE INDEX IF NOT EXISTS idx_lvar_warehouse_default ON listing_variations(warehouse_default);

-- ---------------------------------------------------------------------
-- 2. Marcar listings de devolución por título (heurística)
-- ---------------------------------------------------------------------
UPDATE listings
   SET warehouse_default = 'devolucion'
 WHERE (
        title ILIKE '%caja abierta%'
     OR title ILIKE '%calidad espejo%'
     OR title ILIKE '%oem 1.1%'
     OR title ILIKE '%espejo ip%'
     OR title ILIKE '%reacondicionad%'
     OR title ILIKE '%refurbished%'
   );

UPDATE listing_variations
   SET warehouse_default = 'devolucion'
 WHERE mlm_id IN (
     SELECT mlm_id FROM listings WHERE warehouse_default = 'devolucion'
   );

-- ---------------------------------------------------------------------
-- 3. Consolidar CAMUFLADA → CAMUFLAJE (duplicado por normalización)
-- ---------------------------------------------------------------------
-- Re-apunta los listings a SKU canónico CAMUFLAJE
UPDATE listings SET sku = 'JBL-CLIP5-CAMUFLAJE' WHERE sku = 'JBL-CLIP5-CAMUFLADA';
UPDATE listing_variations SET sku = 'JBL-CLIP5-CAMUFLAJE' WHERE sku = 'JBL-CLIP5-CAMUFLADA';

-- Archivar el SKU duplicado
UPDATE products
   SET archived = true,
       archived_at = now(),
       notes = COALESCE(notes,'') || ' | Consolidado en JBL-CLIP5-CAMUFLAJE 2026-05-17'
 WHERE sku = 'JBL-CLIP5-CAMUFLADA';

-- ---------------------------------------------------------------------
-- 4. Función resolve_sale_target(mlm_id, variation_id) → {sku, warehouse}
-- ---------------------------------------------------------------------
DROP FUNCTION IF EXISTS resolve_sale_target(text, bigint);
CREATE OR REPLACE FUNCTION resolve_sale_target(p_mlm_id text, p_variation_id bigint DEFAULT NULL)
RETURNS TABLE(sku text, warehouse text)
LANGUAGE plpgsql STABLE AS $$
DECLARE
    r_sku       text;
    r_warehouse text;
BEGIN
    -- Prioridad 1: listing_variations por (mlm, vid)
    IF p_variation_id IS NOT NULL THEN
        SELECT lv.sku, lv.warehouse_default INTO r_sku, r_warehouse
          FROM listing_variations lv
         WHERE lv.mlm_id = p_mlm_id
           AND lv.variation_id = p_variation_id
         LIMIT 1;
        IF r_sku IS NOT NULL THEN
            sku := r_sku; warehouse := r_warehouse;
            RETURN NEXT;
            RETURN;
        END IF;
    END IF;

    -- Prioridad 2: listings (single-variation)
    SELECT l.sku, l.warehouse_default INTO r_sku, r_warehouse
      FROM listings l
     WHERE l.mlm_id = p_mlm_id
     LIMIT 1;
    IF r_sku IS NOT NULL THEN
        sku := r_sku; warehouse := r_warehouse;
        RETURN NEXT;
    END IF;
END;
$$;

COMMENT ON FUNCTION resolve_sale_target(text, bigint) IS
'Devuelve (sku, warehouse) para una venta. Prioriza listing_variations(mlm,vid), fallback a listings(mlm). Warehouse = devolucion si listing marca devolucion, else bodega_main.';

-- ---------------------------------------------------------------------
-- 5. Vista helper: listings de devolución
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_listings_devolucion AS
SELECT
    l.mlm_id, l.sku, l.title, l.price, l.status, a.nickname AS account
  FROM listings l
  JOIN accounts a ON a.id = l.account_id
 WHERE l.warehouse_default = 'devolucion';

INSERT INTO schema_migrations(id, description)
VALUES ('sprint1_warehouse_routing_v1', 'warehouse_default en listings/listing_variations + resolve_sale_target + consolidación CAMUFLADA')
ON CONFLICT (id) DO NOTHING;

COMMIT;
