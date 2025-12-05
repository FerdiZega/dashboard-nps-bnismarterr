-- sql_schema.sql
CREATE TABLE IF NOT EXISTS nps_data (
  id BIGSERIAL PRIMARY KEY,
  id_nps TEXT,            -- optional original id
  person_id TEXT NOT NULL,
  nama TEXT,
  kategori TEXT,
  skor_nps NUMERIC,      -- gunakan numeric / integer sesuai sumber
  created_at TIMESTAMP DEFAULT now()
);

-- Indexes for faster aggregations & filters
CREATE INDEX IF NOT EXISTS idx_nps_kategori ON nps_data(kategori);
CREATE INDEX IF NOT EXISTS idx_nps_person ON nps_data(person_id);
CREATE INDEX IF NOT EXISTS idx_nps_score ON nps_data(skor_nps);

-- If you expect huge growth, consider partitioning by year/month (example)
-- CREATE TABLE nps_data_y2025 PARTITION OF nps_data FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
