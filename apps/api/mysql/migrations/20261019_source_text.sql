-- Apply explicitly before enabling source-text imports. Existing sources/claims stay intact.
CREATE TABLE IF NOT EXISTS source_text (
  source_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  archive_url_sha256 CHAR(64) NOT NULL,
  archive_url TEXT NOT NULL,
  content LONGTEXT NOT NULL,
  content_sha256 CHAR(64) NOT NULL,
  archive_blob_sha256 CHAR(64) NOT NULL,
  archive_commit CHAR(40) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (source_id, archive_url_sha256),
  KEY source_text_archive (archive_url_sha256),
  FOREIGN KEY (source_id) REFERENCES source(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
