DELIMITER $$

CREATE TABLE `source` (
  `author` LONGTEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `edition` LONGTEXT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `note` LONGTEXT NULL,
  `source_type` VARCHAR(32) NOT NULL,
  `title` LONGTEXT NOT NULL,
  `url` LONGTEXT NULL,
  PRIMARY KEY (`id`),
  CHECK (source_type IN ('primary','reference','scholarship','digital','media'))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `person` (
  `aliases` JSON NULL DEFAULT (JSON_ARRAY()),
  `biography` LONGTEXT NULL,
  `birth_year` INT NULL,
  `courtesy_name` LONGTEXT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `death_year` INT NULL,
  `description` LONGTEXT NULL,
  `era` LONGTEXT NULL,
  `faction` LONGTEXT NULL,
  `family` JSON NULL DEFAULT (JSON_ARRAY()),
  `historical_evaluation` LONGTEXT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `image_url` LONGTEXT NULL,
  `name` LONGTEXT NOT NULL,
  `native_place` LONGTEXT NULL,
  `references` JSON NULL DEFAULT (JSON_ARRAY()),
  `social_relations` JSON NULL DEFAULT (JSON_ARRAY()),
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  `tags` JSON NULL DEFAULT (JSON_ARRAY()),
  PRIMARY KEY (`id`),
  CHECK (status IN ('draft','published')),
  KEY `published_page` (`status`,`id`),
  KEY `person_name` (`name`(100))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `event` (
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `description` LONGTEXT NULL,
  `dynasty` LONGTEXT NULL,
  `end_year` INT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `image_url` LONGTEXT NULL,
  `impact_level` INT NULL,
  `location_lat` DOUBLE NULL,
  `location_lng` DOUBLE NULL,
  `location_modern_name` LONGTEXT NULL,
  `location_name` LONGTEXT NULL,
  `location_note` LONGTEXT NULL,
  `location_precision` VARCHAR(16) NOT NULL DEFAULT 'unknown',
  `phases` JSON NULL DEFAULT (JSON_ARRAY()),
  `references` JSON NULL DEFAULT (JSON_ARRAY()),
  `start_year` INT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  `tags` JSON NULL DEFAULT (JSON_ARRAY()),
  `time_original` LONGTEXT NULL,
  `title` LONGTEXT NOT NULL,
  PRIMARY KEY (`id`),
  CHECK (status IN ('draft','published')),
  CHECK (impact_level BETWEEN 1 AND 5),
  CHECK (location_precision IN ('site','approximate','region','unknown')),
  CHECK ((location_lat IS NULL) = (location_lng IS NULL)),
  CHECK (location_lat BETWEEN -90 AND 90),
  CHECK (location_lng BETWEEN -180 AND 180),
  CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year),
  KEY `published_page` (`status`,`id`),
  KEY `event_years` (`status`,`start_year`,`end_year`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `topic` (
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `description` LONGTEXT NOT NULL DEFAULT (''),
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `sections` JSON NOT NULL DEFAULT (JSON_ARRAY()),
  `slug` VARCHAR(255) NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  `title` LONGTEXT NOT NULL,
  PRIMARY KEY (`id`),
  CHECK (status IN ('draft','published')),
  CHECK (JSON_TYPE(sections) = 'ARRAY'),
  CHECK (REGEXP_LIKE(slug, '^[a-z0-9]+(-[a-z0-9]+)*$', 'c')),
  UNIQUE KEY `topic_slug` (`slug`),
  KEY `published_page` (`status`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `person_relationship` (
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `description` LONGTEXT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `person_a` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `person_b` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `relation_type` LONGTEXT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`person_a`) REFERENCES `person` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`person_b`) REFERENCES `person` (`id`) ON DELETE CASCADE,
  CHECK (status IN ('draft','published')),
  KEY `published_page` (`status`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `person_event` (
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `event_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `person_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `role` LONGTEXT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`person_id`) REFERENCES `person` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`event_id`) REFERENCES `event` (`id`) ON DELETE CASCADE,
  CHECK (status IN ('draft','published')),
  KEY `published_page` (`status`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `event_causality` (
  `cause_event_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `description` LONGTEXT NULL,
  `effect_event_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`cause_event_id`) REFERENCES `event` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`effect_event_id`) REFERENCES `event` (`id`) ON DELETE CASCADE,
  CHECK (status IN ('draft','published')),
  KEY `published_page` (`status`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TABLE `fact_claim` (
  `citation` LONGTEXT NULL,
  `claim_text` LONGTEXT NOT NULL,
  `confidence` DECIMAL(3,2) NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `field_path` VARCHAR(255) NOT NULL,
  `id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `note` LONGTEXT NULL,
  `source_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
  `subject_id` CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `subject_table` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`source_id`) REFERENCES `source` (`id`) ON DELETE SET NULL,
  CHECK (status IN ('draft','published')),
  CHECK (confidence BETWEEN 0 AND 1),
  KEY `published_page` (`status`,`id`),
  KEY `claim_subject` (`subject_table`,`subject_id`,`status`,`id`),
  KEY `claim_source` (`source_id`,`status`,`id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin$$

CREATE TRIGGER `event_causality_no_self_insert` BEFORE INSERT ON `event_causality` FOR EACH ROW BEGIN IF NEW.cause_event_id = NEW.effect_event_id THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An event cannot cause itself'; END IF; END$$

CREATE TRIGGER `event_causality_no_self_update` BEFORE UPDATE ON `event_causality` FOR EACH ROW BEGIN IF NEW.cause_event_id = NEW.effect_event_id THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An event cannot cause itself'; END IF; END$$

DELIMITER ;
