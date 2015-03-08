-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


CREATE TABLE tournaments (
  id   SERIAL PRIMARY KEY,
  name TEXT
);

CREATE TABLE players (
  id         SERIAL PRIMARY KEY,
  name       TEXT                                NOT NULL,
  tournament INTEGER REFERENCES tournaments (id) NOT NULL
);

CREATE TABLE matches (
  id         SERIAL PRIMARY KEY,
  tournament INTEGER REFERENCES tournaments (id),
  player1    INTEGER REFERENCES players (id) NOT NULL,
  player2    INTEGER REFERENCES players (id),
  winner     INTEGER REFERENCES players (id) NOT NULL,
  CHECK (player1 != player2)
);

CREATE VIEW standings AS
  SELECT
    p.tournament,
    p.id                                                             AS player_id,
    p.name                                                           AS player_name,
    count(CASE WHEN p.id = m.winner THEN 1 END)                      AS wins,
    count(CASE WHEN m.winner IS NULL THEN 1 END)                     AS draws,
    count(CASE WHEN p.id = m.player1 OR p.id = m.player2 THEN 1 END) AS total_matches
  FROM players AS p
    LEFT JOIN matches AS m
      ON p.id = m.player1 OR p.id = m.player2
  GROUP BY p.id, p.name;