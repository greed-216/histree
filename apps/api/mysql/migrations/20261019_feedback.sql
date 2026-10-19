-- Explicit migration; submissions are private and never enter public catalogues.
CREATE TABLE IF NOT EXISTS feedback (
  id CHAR(36) NOT NULL PRIMARY KEY,
  claim_id CHAR(36) NULL,
  source_id CHAR(36) NULL,
  page_path VARCHAR(1024) NOT NULL,
  context_label VARCHAR(500) NOT NULL,
  message TEXT NOT NULL,
  email VARCHAR(254) NULL,
  request_sha256 CHAR(64) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'new',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  KEY feedback_queue (status, created_at),
  KEY feedback_claim (claim_id),
  KEY feedback_source (source_id)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
