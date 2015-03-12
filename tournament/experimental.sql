
-- Since python out performed these queries, they were not implemented in the application

-- Returns swiss pairings for even number players.
EXPLAIN ANALYZE WITH rankings AS
(SELECT row_number() OVER () AS row, * FROM standings WHERE tournament = 1),
    right_players AS
  (SELECT * FROM rankings AS r WHERE r.row % 2 = 0),
    left_players AS
  (SELECT * FROM rankings AS l WHERE l.row % 2 = 1)
SELECT
  l.player_id, l.player_name,
  r.player_id, r.player_name
FROM left_players as l LEFT JOIN right_players AS r ON l.row + 1 = r.row;

-- Returns swiss pairings for odd number players.
EXPLAIN ANALYZE WITH
    rankings AS (
      SELECT * FROM standings WHERE tournament = 1),

    next_bye AS (
      SELECT * FROM rankings WHERE player_id NOT IN
                                   (SELECT player1 FROM matches WHERE tournament = 1 AND player2 is NULL) ORDER BY wins LIMIT 1),

    filter_rankings AS (
      SELECT r.* FROM rankings as r, next_bye AS n WHERE r.player_id != n.player_id),

    new_rankings AS (
      SELECT row_number() OVER() AS row, * FROM (SELECT * FROM filter_rankings UNION ALL SELECT * FROM next_bye) AS players),

    right_players AS (
      SELECT * FROM new_rankings AS r WHERE r.row % 2 = 0),

    left_players AS (
      SELECT * FROM new_rankings AS l WHERE l.row % 2 = 1)

SELECT
  l.player_id, l.player_name,
  r.player_id, r.player_name

FROM left_players as l LEFT JOIN right_players AS r ON l.row + 1 = r.row