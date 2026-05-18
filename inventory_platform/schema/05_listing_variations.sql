-- =====================================================================
-- Variation-aware listings — mapeo por (mlm_id, variation_id) → sku
-- =====================================================================
-- Para listings multi-color en MELI: un MLM tiene N variations, cada una
-- con su color/atributos. Cuando llega orden, MELI manda variation_id.
-- process_event.py consulta esta tabla primero, luego cae a listings.sku.
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS listing_variations (
    mlm_id          text NOT NULL,
    variation_id    bigint NOT NULL,
    sku             text NOT NULL REFERENCES products(sku) ON DELETE RESTRICT,
    color           text,
    attribute_combinations jsonb,
    price           numeric(10,2),
    available_quantity int,
    sold_quantity   int DEFAULT 0,
    last_sync       timestamptz DEFAULT now(),
    created_at      timestamptz DEFAULT now(),
    PRIMARY KEY (mlm_id, variation_id)
);

CREATE INDEX IF NOT EXISTS idx_lvar_sku ON listing_variations(sku);
CREATE INDEX IF NOT EXISTS idx_lvar_mlm ON listing_variations(mlm_id);

COMMENT ON TABLE listing_variations IS
'Variation-aware mapeo MELI listing+variation → SKU canónico. process_event.py consulta primero por (mlm_id, variation_id), fallback a listings.sku.';

-- ---------------------------------------------------------------------
-- Función helper: resolver SKU por (mlm_id, variation_id|NULL)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION resolve_sku(p_mlm_id text, p_variation_id bigint DEFAULT NULL)
RETURNS text LANGUAGE sql STABLE AS $$
    SELECT COALESCE(
        -- 1. Match exacto en listing_variations
        (SELECT sku FROM listing_variations
          WHERE mlm_id = p_mlm_id AND variation_id = p_variation_id
          LIMIT 1),
        -- 2. Fallback a listings (single-variation o pre-variation-aware)
        (SELECT sku FROM listings WHERE mlm_id = p_mlm_id LIMIT 1)
    );
$$;

COMMENT ON FUNCTION resolve_sku(text, bigint) IS
'Resuelve SKU de una venta: primero busca listing_variations(mlm,variation), luego listings(mlm). NULL si no mapeado.';

INSERT INTO schema_migrations(id, description)
VALUES ('sprint1_listing_variations_v1', 'Variation-aware mapping + resolve_sku() function')
ON CONFLICT (id) DO NOTHING;

COMMIT;
