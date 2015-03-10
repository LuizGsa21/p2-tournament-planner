-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP VIEW IF EXISTS standings;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS tournaments;

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
    p.id                         AS player_id,
    p.name                       AS player_name,
    COALESCE(s.wins, 0)          AS wins,
    COALESCE(s.total_matches, 0) AS total_matches
  FROM players AS p
    LEFT JOIN (SELECT
                 p.id,
                 count(CASE WHEN p.id = m.winner THEN 1 END)                      AS wins,
                 count(CASE WHEN p.id = m.player1 OR p.id = m.player2 THEN 1 END) AS total_matches
               FROM players AS p,
                 matches AS m
               WHERE p.id = m.player1 OR p.id = m.player2
               GROUP BY p.tournament, p.id, p.name) AS s ON p.id = s.id;


CREATE OR REPLACE FUNCTION get_OMW(INTEGER, INTEGER) RETURNS NUMERIC
AS 'SELECT sum(standings.wins)
    FROM
      (SELECT DISTINCT CASE
                       WHEN $1 = player1 THEN player2
                        ELSE player1
                       END AS id
          FROM matches
          WHERE tournament = $2 AND
                (player1 = $1 OR player2 = $1)) AS op
      LEFT JOIN standings ON op.id = player_id;'
LANGUAGE SQL
STABLE
RETURNS NULL ON NULL INPUT;