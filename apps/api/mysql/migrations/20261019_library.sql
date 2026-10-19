-- Explicit migration. Reading availability is independent from historical fact publication.
CREATE TABLE IF NOT EXISTS library_book (
  book_key VARCHAR(64) NOT NULL PRIMARY KEY,
  title VARCHAR(100) NOT NULL,
  source_version VARCHAR(64) NOT NULL,
  sort_order INT NOT NULL,
  section_count INT NOT NULL,
  paragraph_count INT NOT NULL,
  dataset_sha256 CHAR(64) NOT NULL,
  metadata JSON NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'draft'
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_asset (
  id CHAR(64) NOT NULL PRIMARY KEY,
  source_file VARCHAR(1024) NOT NULL,
  source_sha256 CHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_section (
  id VARCHAR(128) NOT NULL PRIMARY KEY,
  book_key VARCHAR(64) NOT NULL,
  sort_order INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  volume INT NULL,
  kind VARCHAR(32) NOT NULL,
  has_issues TINYINT NOT NULL,
  metadata JSON NOT NULL,
  UNIQUE KEY library_section_order (book_key,sort_order),
  FOREIGN KEY (book_key) REFERENCES library_book(book_key) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_paragraph (
  id VARCHAR(128) NOT NULL PRIMARY KEY,
  book_key VARCHAR(64) NOT NULL,
  section_id VARCHAR(128) NOT NULL,
  ordinal INT NOT NULL,
  kind VARCHAR(32) NOT NULL,
  content LONGTEXT NOT NULL,
  content_sha256 CHAR(64) NOT NULL,
  asset_id CHAR(64) NOT NULL,
  char_start BIGINT NOT NULL,
  char_end BIGINT NOT NULL,
  flags JSON NOT NULL,
  UNIQUE KEY library_book_order (book_key,ordinal),
  KEY library_section_page (section_id,ordinal),
  KEY library_content_hash (content_sha256),
  FOREIGN KEY (book_key) REFERENCES library_book(book_key) ON DELETE RESTRICT,
  FOREIGN KEY (section_id) REFERENCES library_section(id) ON DELETE RESTRICT,
  FOREIGN KEY (asset_id) REFERENCES library_asset(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_source_link (
  source_id CHAR(36) NOT NULL,
  archive_url_sha256 CHAR(64) NOT NULL,
  snapshot_sha256 CHAR(64) NOT NULL,
  paragraph_id VARCHAR(128) NOT NULL,
  PRIMARY KEY (source_id,archive_url_sha256),
  FOREIGN KEY (paragraph_id) REFERENCES library_paragraph(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
