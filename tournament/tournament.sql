-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


CREATE TABLE players (
  id   SERIAL PRIMARY KEY,
  name TEXT
);

CREATE TABLE matches (
  id        SERIAL PRIMARY KEY,
  winner_id INTEGER REFERENCES players (id),
  loser_id  INTEGER REFERENCES players (id)
);

CREATE VIEW standings AS
  SELECT
    p.id                                                                AS player_id,
    p.name                                                              AS player_name,
    count(CASE WHEN p.id = m.winner_id THEN 1 END)                      AS wins,
    count(CASE WHEN p.id = m.winner_id OR p.id = m.loser_id THEN 1 END) AS totat_matches
  FROM players AS p
    LEFT JOIN matches AS m
      ON p.id = m.winner_id OR p.id = m.loser_id
  GROUP BY p.id, p.name;