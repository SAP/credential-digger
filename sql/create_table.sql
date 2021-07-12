CREATE TYPE STATES AS ENUM ('new', 'false_positive', 'addressing', 'not_relevant', 'fixed');

CREATE TABLE repos (
  url TEXT NOT NULL UNIQUE,
  last_scan INTEGER,
  PRIMARY KEY (url)
);

CREATE TABLE rules (
  id SERIAL NOT NULL UNIQUE,
  regex TEXT NOT NULL UNIQUE,
  category VARCHAR(50),
  description TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE discoveries (
  id SERIAL NOT NULL UNIQUE,
  file_name TEXT NOT NULL,
  commit_id TEXT NOT NULL,
  line_number INTEGER DEFAULT -1,
  snippet TEXT DEFAULT '',
  repo_url TEXT,
  rule_id INTEGER,
  state STATES NOT NULL DEFAULT 'new',
  timestamp TEXT NOT NULL DEFAULT timeofday(),
  PRIMARY KEY (id),
  FOREIGN KEY (repo_url) REFERENCES repos ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (rule_id) REFERENCES rules ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE embeddings (
  id INTEGER REFERENCES discoveries,
  embedding FLOAT [],
  snippet TEXT,
  repo_url TEXT REFERENCES repos,
  PRIMARY KEY (id)
);
