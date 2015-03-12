-- Table definitions for the tournament project.

DROP VIEW IF EXISTS standings;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;
DROP FUNCTION IF EXISTS get_played_opponents(INTEGER, INTEGER);
DROP TABLE IF EXISTS tournaments;

-- Tournament
-- Used for registering tournaments
CREATE TABLE tournaments (
  id   SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

-- Players
-- Used for registering players.
CREATE TABLE players (
  id         SERIAL PRIMARY KEY,
  name       TEXT                                NOT NULL,
  tournament INTEGER REFERENCES tournaments (id) NOT NULL
);

-- Matches
-- id: used for differentiating a rematch.
-- tournament: registered tournament id
-- player1: player playing in match.
-- player2: player playing in match OR a NULL value to represent a bye player
-- winner: the match winner OR a NULL value to represent a draw
CREATE TABLE matches (
  id         SERIAL PRIMARY KEY,
  tournament INTEGER REFERENCES tournaments (id) NOT NULL,
  player1    INTEGER REFERENCES players (id) NOT NULL,
  player2    INTEGER REFERENCES players (id),
  winner     INTEGER REFERENCES players (id),
  -- A player can't play against himself
  CHECK (player1 != player2)
);

-- Returns an array of played opponents from the given player. ByePlayers are represented with null values
-- args:
--    players.id - the given player
--    tournament.id - the tournament to search in
CREATE OR REPLACE FUNCTION get_played_opponents(player_id INTEGER, tournament_id INTEGER)
  RETURNS INTEGER []
AS 'SELECT ARRAY(SELECT
                   DISTINCT CASE
                            WHEN $1 = player1 THEN player2
                            ELSE player1
                            END AS id
                 FROM matches
                 WHERE (tournament = $2) AND (player1 = $1 OR player2 = $1))'
LANGUAGE SQL
STABLE
RETURNS NULL ON NULL INPUT;

-- Standings
-- columns returned: tournament, player_id, player_name, wins, total_matches, omw (Opponent match wins)
CREATE VIEW standings AS
  -- Create a CTE for player's id, wins, total match count and an array of played opponents
  -- When a player hasn't played a match, the following columns return NULL: wins, total_matches, played_opponents
  WITH scores AS (
      SELECT
        p.id,
        p.tournament,
        count(CASE WHEN p.id = m.winner THEN 1 END)                      AS wins,
        count(CASE WHEN p.id = m.player1 OR p.id = m.player2 THEN 1 END) AS total_matches,
        get_played_opponents(p.id, p.tournament)                         AS played_opponents
      FROM players AS p,
        matches AS m
      WHERE (p.tournament = m.tournament) AND (p.id = m.player1 OR p.id = m.player2)
      GROUP BY p.id)
  SELECT
    p.tournament,
    p.id                                               AS player_id,
    p.name                                             AS player_name,
    -- Use coalesce to filter out null columns returned from `scores`
    COALESCE(s.wins, 0)                                AS wins,
    COALESCE(s.total_matches, 0)                       AS total_matches,
    -- To get OMW, use `scores` to get played opponents, then calculate the sum from the wins column.
    COALESCE((SELECT sum(wins)
              FROM scores
              WHERE id = ANY ((SELECT played_opponents
                               FROM scores
                               WHERE id = p.id) :: INTEGER [])), 0) AS omw
  FROM players AS p
    LEFT JOIN scores AS s ON p.tournament = s.tournament AND p.id = s.id
  ORDER BY wins DESC, omw DESC, player_id;
