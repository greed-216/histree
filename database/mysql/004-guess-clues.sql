-- Additive GAME data only. Does not create historical people/claims or change book progress.
-- Identity mapping is explicit. Equal names alone never merge historical identities.
CREATE TABLE guess_character (
  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  canonical_person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
  name VARCHAR(100) NOT NULL,
  aliases JSON NOT NULL,
  courtesy_name VARCHAR(100) NULL,
  era VARCHAR(100) NULL,
  birth_year INT NULL,
  death_year INT NULL,
  period_from INT NULL,
  period_to INT NULL,
  description TEXT NOT NULL,
  difficulty VARCHAR(8) NOT NULL DEFAULT 'hard',
  knowledge_revision INT UNSIGNED NOT NULL DEFAULT 1,
  difficulty_revision INT UNSIGNED NOT NULL DEFAULT 1,
  question_difficulty VARCHAR(8) NOT NULL DEFAULT 'hard',
  question_revision INT UNSIGNED NOT NULL DEFAULT 1,
  question_vote_clue_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  question_easy_votes INT UNSIGNED NOT NULL DEFAULT 0,
  question_right_votes INT UNSIGNED NOT NULL DEFAULT 0,
  question_hard_votes INT UNSIGNED NOT NULL DEFAULT 0,
  vote_clue_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  easy_votes INT UNSIGNED NOT NULL DEFAULT 0,
  right_votes INT UNSIGNED NOT NULL DEFAULT 0,
  hard_votes INT UNSIGNED NOT NULL DEFAULT 0,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY(id),
  UNIQUE KEY guess_character_canonical(canonical_person_id),
  FOREIGN KEY(canonical_person_id) REFERENCES person(id) ON DELETE RESTRICT,
  CHECK(difficulty IN ('easy','hard')),
  CHECK(knowledge_revision>0),
  CHECK(difficulty_revision>0),
  CHECK(question_revision>0),
  CHECK(question_difficulty IN ('easy','hard')),
  CHECK(period_from IS NULL OR period_to IS NULL OR period_from<=period_to),
  CHECK(birth_year IS NULL OR death_year IS NULL OR birth_year<=death_year),
  KEY guess_character_level(enabled,difficulty,id)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;

-- Reuse the existing bank's identity and initial difficulty. No AI or source-coverage gate.
INSERT INTO guess_character(id,canonical_person_id,name,aliases,courtesy_name,era,birth_year,death_year,description,difficulty,question_difficulty)
SELECT p.id,p.id,p.name,COALESCE(p.aliases,JSON_ARRAY()),p.courtesy_name,p.era,p.birth_year,p.death_year,COALESCE(p.description,''),b.difficulty,b.difficulty
FROM guess_bank b JOIN person p ON p.id=b.person_id WHERE p.status='published';

CREATE TABLE guess_clue_set (
  person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  profile_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  generator_version SMALLINT UNSIGNED NOT NULL,
  status VARCHAR(12) NOT NULL,
  clues JSON NULL,
  provenance JSON NULL,
  lease_token CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
  lease_until DATETIME(6) NULL,
  retry_after DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (person_id,profile_revision,generator_version),
  FOREIGN KEY (person_id) REFERENCES guess_character(id) ON DELETE CASCADE,
  CHECK (generator_version>0),
  CHECK (status IN ('generating','ready','failed')),
  CHECK ((status='ready' AND clues IS NOT NULL AND JSON_TYPE(clues)='ARRAY' AND JSON_LENGTH(clues)=6)
    OR (status<>'ready' AND clues IS NULL)),
  CHECK ((status='generating' AND lease_token IS NOT NULL AND lease_until IS NOT NULL)
    OR (status<>'generating' AND lease_token IS NULL AND lease_until IS NULL)),
  KEY guess_clue_ready (generator_version,status,person_id)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;

-- Difficulty votes for clue mode. Historical identities may be absent.
CREATE TABLE guess_clue_feedback (
  game_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  clue_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  difficulty_revision INT UNSIGNED NOT NULL,
  actor_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  rating VARCHAR(8) NOT NULL,
  guesses TINYINT UNSIGNED NOT NULL,
  unlocked TINYINT UNSIGNED NOT NULL,
  outcome VARCHAR(12) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY(game_hash),
  UNIQUE KEY guess_clue_vote_actor(person_id,clue_revision,difficulty_revision,actor_hash),
  FOREIGN KEY(person_id) REFERENCES guess_character(id) ON DELETE CASCADE,
  CHECK(rating IN ('easy','right','hard')),
  CHECK(difficulty_revision>0),
  CHECK(guesses<=80),
  CHECK(unlocked BETWEEN 1 AND 6),
  CHECK(guesses>0 OR unlocked>1),
  CHECK(outcome IN ('won','revealed'))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;

-- Question-mode votes for game characters without a legacy bank record.
CREATE TABLE guess_question_feedback (
  game_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  person_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  clue_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  difficulty_revision INT UNSIGNED NOT NULL,
  actor_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  rating VARCHAR(8) NOT NULL,
  guesses TINYINT UNSIGNED NOT NULL,
  unlocked TINYINT UNSIGNED NOT NULL,
  outcome VARCHAR(12) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY(game_hash),
  UNIQUE KEY guess_question_vote_actor(person_id,clue_revision,difficulty_revision,actor_hash),
  FOREIGN KEY(person_id) REFERENCES guess_character(id) ON DELETE CASCADE,
  CHECK(rating IN ('easy','right','hard')),
  CHECK(difficulty_revision>0),
  CHECK(guesses<=80),
  CHECK(unlocked BETWEEN 1 AND 6),
  CHECK(guesses>0 OR unlocked>1),
  CHECK(outcome IN ('won','revealed','limit'))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
