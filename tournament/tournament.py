#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def startNewTournament(name):
    """Starts a new tournament with the given. Returns it's unique id.
    Parameters:
     name: Tournament name
    Returns:
        int - Tournament's unique id
    """
    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO tournaments (name) VALUES (%s)', (name,))
    db.commit()
    db.close()
    return getCurrentTournamentId()


def getCurrentTournamentId():
    """Returns the current tournament's unique id.
    Throws a ValueError exception when no tournament is found.

    Returns:
      int - Tournament's unique id
    """
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM tournaments ORDER BY id DESC LIMIT 1')
    id = cursor.fetchone()
    if id is None:
        raise ValueError('No tournament was found in the database.')
    db.close()
    return id[0]


def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute('DELETE FROM matches')
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute('DELETE FROM players')
    db.commit()
    db.close()


def countPlayers():
    """Returns the number of players currently registered."""
    tournament = getCurrentTournamentId()
    db = connect()
    cursor = db.cursor()
    cursor.execute('SELECT count(id) AS total_players FROM players WHERE tournament = %s', (tournament,))
    count = cursor.fetchone()[0]
    db.close()
    return count


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    tournament = getCurrentTournamentId()

    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO players (name, tournament) VALUES (%s, %s)', (name, tournament))
    db.commit()
    db.close()


def playerStandings(allTournaments=False):
    """Returns a list of the players and their win records, sorted by wins
    for the current tournament.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Parameters:
     allTournaments:
        boolean Default = False
        Set to True to receive player standings for all tournaments
    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    db = connect()
    cursor = db.cursor()
    if allTournaments:
        cursor.execute("""SELECT player_id, player_name, wins, total_matches
                          FROM standings
                          ORDER BY wins DESC, omw DESC, player_id""")
    else:
        tournament = getCurrentTournamentId()
        cursor.execute("""SELECT player_id, player_name, wins, total_matches
                          FROM standings
                          WHERE tournament = %s ORDER BY wins DESC, omw DESC, player_id""", (tournament,))
    standings = cursor.fetchall()
    db.close()
    return standings


def reportMatch(player1, player2, isDraw=False):
    """Records the outcome of a single match between two players.

    Player1 wins when player2 is null OR isDraw == False
    Player2 wins when player1 is null.

    A draw is not reported if both players are null.

    Args:
      player1: default winner
      player2: default loser
      isDraw: set to true to report a draw match.
    Returns:
      Boolean: True if match was reported, false otherwise.
    """
    if player1 is None:
        if player2 is None:
            return False
        else:
            winner = player2
    elif player2 is None or isDraw is False:
        winner = player1
    else:
        winner = None

    tournament = getCurrentTournamentId()

    db = connect()
    cursor = db.cursor()
    cursor.execute('INSERT INTO matches (tournament, winner, player1, player2) VALUES (%s, %s, %s, %s)',
                   (tournament, winner, player1, player2))
    db.commit()
    db.close()
    return True


def getOddPairingMatches():
    db = connect()
    cursor = db.cursor()
    cursor.execute("""WITH rankings AS (SELECT player_id, player_name, wins, total_matches
                                        FROM standings WHERE tournament = %s
                                        ORDER BY wins DESC, omw DESC, player_id),
                           byeplayer AS (SELECT r.*
                                         FROM rankings AS r
                                         WHERE r.player_id NOT IN (SELECT m.player1
                                                                   FROM matches AS m
                                                                   WHERE m.player1 = r.player_id AND player2 IS NULL) ORDER BY wins LIMIT 1)
                        SELECT  r.*
                        FROM rankings AS r, byeplayer AS b
                        WHERE r.player_id != b.player_id
                        UNION ALL
                        SELECT * FROM byeplayer
                        UNION ALL
                        SELECT NULL, NULL, NULL, NULL""", (getCurrentTournamentId(),))
    pairings = cursor.fetchall()
    db.close()

    if pairings[0][0] is None:
        raise ValueError('No possible bye player found.')

    return pairings


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    playerCount = countPlayers()
    if playerCount % 2 == 1:
        standings = getOddPairingMatches()
    else:
        standings = playerStandings()

    return [(p1[0], p1[1], p2[0], p2[1]) for p1, p2 in zip(standings[::2], standings[1::2])]

