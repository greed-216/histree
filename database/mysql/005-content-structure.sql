-- Explicit additive migration. Existing historical rows and dates are never rewritten.
CREATE TABLE IF NOT EXISTS claim_structure (
 claim_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 note_sha256 CHAR(64) NOT NULL, quote_text LONGTEXT NOT NULL, review_note LONGTEXT NOT NULL,
 review_state ENUM('recorded','deferred','unparsed') NOT NULL,
 FOREIGN KEY (claim_id) REFERENCES fact_claim(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS event_dating (
 id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 event_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 claim_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 claim_sha256 CHAR(64) NOT NULL,
 earliest_year INT NULL, latest_year INT NULL,
 precision_kind ENUM('year','approximate','range','relative','era','unknown') NOT NULL,
 era_key VARCHAR(100) NULL, basis LONGTEXT NOT NULL,
 review_state ENUM('proposed','reviewed') NOT NULL DEFAULT 'proposed',
 CHECK(earliest_year IS NULL OR earliest_year BETWEEN -10000 AND 10000 AND earliest_year<>0),
 CHECK(latest_year IS NULL OR latest_year BETWEEN -10000 AND 10000 AND latest_year<>0),
 CHECK(earliest_year IS NULL OR latest_year IS NULL OR earliest_year<=latest_year),
 CHECK(precision_kind NOT IN ('year','range','approximate') OR earliest_year IS NOT NULL AND latest_year IS NOT NULL),
 CHECK(precision_kind<>'year' OR earliest_year=latest_year),
 CHECK(precision_kind<>'era' OR era_key IS NOT NULL),
 KEY dating_lookup(event_id,review_state), KEY dating_range(review_state,earliest_year,latest_year),
 FOREIGN KEY(event_id) REFERENCES event(id) ON DELETE RESTRICT,
 FOREIGN KEY(claim_id) REFERENCES fact_claim(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_review_coverage (
 book_key VARCHAR(64) NOT NULL, source_version VARCHAR(64) NOT NULL, volume INT NOT NULL,
 reviewed INT NOT NULL, published INT NOT NULL, no_new INT NOT NULL, deferred INT NOT NULL,
 audit_sha256 CHAR(64) NOT NULL, audit_path VARCHAR(1024) NOT NULL,
 PRIMARY KEY(book_key,source_version,volume),
 CHECK(reviewed>=0 AND published>=0 AND no_new>=0 AND deferred>=0),
 CHECK(published+no_new<=reviewed AND deferred<=reviewed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS library_paragraph_review (
 paragraph_id VARCHAR(128) PRIMARY KEY, content_sha256 CHAR(64) NOT NULL,
 disposition ENUM('published','no_new','deferred') NOT NULL,
 reason LONGTEXT NOT NULL, audit_sha256 CHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS claim_relation (
 id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 claim_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 related_claim_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 claim_sha256 CHAR(64) NOT NULL, related_sha256 CHAR(64) NOT NULL,
 relation_kind ENUM('corroborates','conflicts','identity_candidate') NOT NULL,
 review_state ENUM('proposed','reviewed') NOT NULL DEFAULT 'proposed',
 note LONGTEXT NOT NULL,
 CHECK(claim_id<>related_claim_id),
 KEY claim_relation_left(claim_id,review_state), KEY claim_relation_right(related_claim_id,review_state),
 FOREIGN KEY(claim_id) REFERENCES fact_claim(id) ON DELETE RESTRICT,
 FOREIGN KEY(related_claim_id) REFERENCES fact_claim(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
CREATE TABLE IF NOT EXISTS content_revision (
 id TINYINT PRIMARY KEY, revision BIGINT UNSIGNED NOT NULL DEFAULT 0, CHECK(id=1)
) ENGINE=InnoDB;
INSERT IGNORE INTO content_revision(id,revision) VALUES(1,0);
CREATE TRIGGER revision_person_insert AFTER INSERT ON person FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_update AFTER UPDATE ON person FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_delete AFTER DELETE ON person FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_insert AFTER INSERT ON event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_update AFTER UPDATE ON event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_delete AFTER DELETE ON event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_fact_claim_insert AFTER INSERT ON fact_claim FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_fact_claim_update AFTER UPDATE ON fact_claim FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_fact_claim_delete AFTER DELETE ON fact_claim FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_source_insert AFTER INSERT ON source FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_source_update AFTER UPDATE ON source FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_source_delete AFTER DELETE ON source FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_relationship_insert AFTER INSERT ON person_relationship FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_relationship_update AFTER UPDATE ON person_relationship FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_relationship_delete AFTER DELETE ON person_relationship FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_event_insert AFTER INSERT ON person_event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_event_update AFTER UPDATE ON person_event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_person_event_delete AFTER DELETE ON person_event FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_causality_insert AFTER INSERT ON event_causality FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_causality_update AFTER UPDATE ON event_causality FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_causality_delete AFTER DELETE ON event_causality FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_claim_structure_insert AFTER INSERT ON claim_structure FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_claim_structure_update AFTER UPDATE ON claim_structure FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_claim_structure_delete AFTER DELETE ON claim_structure FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_dating_insert AFTER INSERT ON event_dating FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_dating_update AFTER UPDATE ON event_dating FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_event_dating_delete AFTER DELETE ON event_dating FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_source_link_insert AFTER INSERT ON library_source_link FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_source_link_update AFTER UPDATE ON library_source_link FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_source_link_delete AFTER DELETE ON library_source_link FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_review_coverage_insert AFTER INSERT ON library_review_coverage FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_review_coverage_update AFTER UPDATE ON library_review_coverage FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_review_coverage_delete AFTER DELETE ON library_review_coverage FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_paragraph_review_insert AFTER INSERT ON library_paragraph_review FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_paragraph_review_update AFTER UPDATE ON library_paragraph_review FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_library_paragraph_review_delete AFTER DELETE ON library_paragraph_review FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
-- Prefix indexes accelerate exact facets without changing historical display strings.
CREATE INDEX person_directory_era ON person(status,era(64),id);
CREATE INDEX person_directory_faction ON person(status,faction(64),id);
CREATE INDEX person_event_chronology ON person_event(status,person_id,event_id);
CREATE TRIGGER revision_claim_relation_insert AFTER INSERT ON claim_relation FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_claim_relation_update AFTER UPDATE ON claim_relation FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
CREATE TRIGGER revision_claim_relation_delete AFTER DELETE ON claim_relation FOR EACH ROW UPDATE content_revision SET revision=revision+1 WHERE id=1;
