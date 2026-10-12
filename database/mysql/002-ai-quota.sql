CREATE TABLE ai_gateway_quota (
    actor VARCHAR(80) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    operation VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    bucket DATETIME NOT NULL,
    used INT NOT NULL,
    PRIMARY KEY(actor,operation,bucket), KEY quota_expiry(bucket),
    CHECK(operation IN ('ask','guess','session')), CHECK(used>=0)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
