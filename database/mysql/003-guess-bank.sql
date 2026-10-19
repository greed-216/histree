-- Explicit additive game migration. Do not replay baseline content DDL.
-- No historical records or publication state are modified.
CREATE TABLE guess_bank (
  person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  difficulty VARCHAR(8) NOT NULL,
  revision INT UNSIGNED NOT NULL DEFAULT 1,
  easy_votes INT UNSIGNED NOT NULL DEFAULT 0,
  right_votes INT UNSIGNED NOT NULL DEFAULT 0,
  hard_votes INT UNSIGNED NOT NULL DEFAULT 0,
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (person_id),
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  CHECK (difficulty IN ('easy','hard')),
  KEY guess_bank_difficulty (difficulty,person_id)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;

CREATE TABLE guess_difficulty_feedback (
  game_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  revision INT UNSIGNED NOT NULL,
  actor_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  rating VARCHAR(8) NOT NULL,
  turns TINYINT UNSIGNED NOT NULL,
  hints TINYINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (game_hash),
  UNIQUE KEY guess_feedback_actor (person_id,revision,actor_hash),
  FOREIGN KEY (person_id) REFERENCES guess_bank(person_id) ON DELETE CASCADE,
  CHECK (rating IN ('easy','right','hard')),
  CHECK (turns BETWEEN 1 AND 30),
  CHECK (hints <= 3)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
